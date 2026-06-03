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
pack even though a better arrangement existed.

## Naive padded baseline

The lab asks for a naive baseline with batch size 4. That means the original
sequence list is split into groups of four, and each group is padded to the
longest sequence in that group.

For one batch:

$$
\text{padded tokens} = 4 \max(L_1,L_2,L_3,L_4)
$$

For the last batch, use its actual size if fewer than four sequences remain.

The total naive padded count is the sum across batches.

## Packed-token count

The starter uses a fixed pack capacity of 1024 tokens. After packing, the packed
token count is:

$$
1024 \times \text{number of packs}
$$

This counts allocated pack capacity, not just useful residues. The useful token
count remains:

$$
\sum_i L_i
$$

The difference between allocated capacity and useful tokens is remaining padding
inside packs.

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
For transformer attention, that usually means a block-diagonal attention mask:

```text
protein A attends to A only
protein B attends to B only
protein C attends to C only
```

If residues from unrelated proteins attend to each other, the packed batch is no
longer equivalent to independent inference. The model may create artificial
contacts or corrupt embeddings.

For protein language model embedding, block-diagonal masking is conceptually
straightforward. For all-atom structure prediction, independence is harder
because pair tensors, chain encodings, template features, and geometry modules
may all need matching masks.

## Relationship to FlashAttention

Packing and FlashAttention solve different problems:

- FlashAttention reduces memory traffic for attention by tiling and using online
  softmax.
- Packing reduces wasted tokens before attention begins.

They combine well. A packed batch can feed a memory-efficient attention kernel,
but the kernel still needs correct sequence-boundary information.

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

In short: pack independent sequence workloads freely once masks are correct;
pack structure workloads only when the model explicitly supports it.
