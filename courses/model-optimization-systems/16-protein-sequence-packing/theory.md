# Padding, bin packing, and masks

Sequence packing is a version of bin packing. Each protein sequence has a
length, each pack has a capacity, and the goal is to use fewer padded token
slots.

The exact bin-packing problem is NP-hard. First-fit decreasing is a standard
heuristic:

1. Sort items from largest to smallest.
2. For each item, scan existing bins in order.
3. Put the item into the first bin where it fits.
4. Open a new bin only when needed.

The decreasing sort helps because large items are the hardest to place. If you
place many tiny items first, a later large sequence may be forced into a new
pack even though a better arrangement existed. Johnson's 1973 analysis shows
FFD uses at most $\frac{11}{9}\,\mathrm{OPT} + 1$ bins; the lab does not ask
you to prove that, but it is why a slightly imperfect packed layout still
counts as a win.

## Naive padded baseline

The lab asks for a naive baseline with batch size 4. That means the original
sequence list is split into groups of four, and each group is padded to the
longest sequence in that group.

For one batch of size $B$:

$$
\text{padded tokens} = B \max(L_1,\ldots,L_B)
$$

For the last batch, use its actual size if fewer than four sequences remain.
The total naive padded count is the sum across batches.

A second baseline, used constantly in practice, is the same counter after
sorting lengths. Length-bucketing is what you do on a Friday afternoon before
reaching for a packer. It is strictly better than arrival-order padding and
strictly worse than FFD on this workload; reporting all three keeps the win
honest.

## Packed-token count

The starter uses a fixed pack capacity of 128 tokens. After packing, the packed
token count is:

$$
128 \times \text{number of packs}
$$

This counts allocated pack capacity, not just useful residues. The useful token
count remains $\sum_i L_i$. The difference is remaining padding inside packs.

Special tokens belong in $L_i$. ESM-2 wraps every sequence in `<cls>` and
`<eos>`, so a 76-residue protein occupies 78 tokens. Budgeting from FASTA
lengths under-counts every pack.

## Waste reduction

The reduction compares naive padding against packed allocation:

$$
\text{reduction} =
\frac{\text{naive padded} - \text{packed tokens}}{\text{naive padded}} \times 100
$$

If packing uses fewer token slots, the percentage is positive. If the pack
capacity is poorly chosen, or if the sequence lengths already batch well, the
improvement may be small.

## Masking is the contract

Packing is only correct when the model cannot leak information across examples.
For transformer attention, that means a block-diagonal attention mask:

```text
protein A attends to A only
protein B attends to B only
protein C attends to C only
```

A 2D padding mask of shape `(batch, seq)` cannot express this. It can zero out
pad tokens, but every real token in the pack remains visible to every other
real token. The packed batch is then a different computation, not a faster
version of independent inference.

HuggingFace's `EsmModel.forward` will not take a 4D mask. It rejects one
outright, and a 3D mask crashes because the embedding layer reuses the tensor
as a per-token padding indicator. The lab therefore splits the call: the 2D
padding mask goes to `embeddings`, and a 4D additive mask
(`0` allowed, `-inf` blocked) goes to `encoder`. That split is an API fact,
not a modelling choice. Other libraries (and other HuggingFace model classes)
accept 4D masks directly; ESM-2 as wrapped today does not.

If residues from unrelated proteins attend to each other, the model may create
artificial contacts or corrupt embeddings. The lab's negative control measures
this at 23% to 64% relative error on real ESM-2 8M outputs — large enough that
no downstream classifier, probe, or retrieval index would be measuring what
you think it is measuring.

## Position IDs are a second, independent contract

Even a perfect attention mask is not enough for every architecture.

Rotary position embeddings, which ESM-2 uses, depend on the difference
$i - j$. A constant offset on a packed segment therefore cancels inside that
segment, and packed embeddings match standalone without any position-id reset.
This is convenient and easy to over-generalize.

Learned absolute position embeddings do not cancel. BERT, T5, and many folding
trunks add $P[i]$ into the token at packed index $i$. If a 40-residue sequence
is placed at offset 80, it receives $P[80], \ldots, P[119]$ instead of
$P[0], \ldots, P[39]$, and every embedding changes. The lab demonstrates this
on a tiny attention block with learned positions: per-segment IDs match 14 of
14; continuous IDs match only the 4 segments that sit at offset 0, and the
other 10 corrupt by up to 144%.

Packing a new model means checking both contracts, not copying the ESM-2
conclusion.

## The quadratic caveat

FlashAttention and packing solve different problems:

- FlashAttention reduces memory traffic for attention by tiling and using
  online softmax.
- Packing reduces wasted tokens before attention begins.

They combine well, but packing has a cost that a padding-waste percentage
conceals. Attention is quadratic in the *kernel's sequence axis*, which for a
dense kernel is the pack capacity, not the useful token count. A pack of
capacity $C$ holding segments of lengths $L_1, \ldots, L_k$ scores:

| Kernel | Score entries |
|---|---|
| dense, packed | $C^2$ |
| block-sparse, packed | $\sum_i L_i^2$ |
| one-at-a-time, no padding | $\sum_i L_i^2$ |
| naive padded batch of rows $S_j$ | $\sum_j S_j^2$ |

On this lab's sequences the dense packed kernel does *more* attention work
than naive padded batching. Packing still wins on the sequence-axis memory
traffic and on kernel-launch overhead (four packs instead of fourteen
forwards), and it wins on compute if and only if the kernel can skip the
masked blocks. A padding-waste percentage that ignores this is a incomplete
argument.

The mask tensor is itself $O(C^2)$ per pack. At $C = 128$ that is 256 KiB in
float32. At $C = 8192$ with 8 packs it is 2 GiB. Production packers therefore
store a bool mask, a list of segment offsets, or nothing at all and let a
block-sparse kernel take the offsets directly.

## Biological examples

Packing is attractive for:

- embedding all proteins in a genome,
- scoring many single-point variants,
- clustering metagenomic proteins,
- precomputing representations for a retrieval index,
- screening peptide libraries.

Packing is risky or model-dependent for:

- co-folding a protein-ligand complex,
- predicting protein-protein interfaces,
- using an MSA tied to a specific query,
- modeling alternative chain stoichiometries,
- predicting all-atom coordinates with pair features.

In short: pack independent sequence workloads freely once both contracts —
attention isolation and position-id reset — have been checked against the
actual model; pack structure workloads only when the model explicitly
supports it.
