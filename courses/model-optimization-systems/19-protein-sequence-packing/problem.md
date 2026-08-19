# Protein sequence packing, verified against ESM-2

The reading argued that packing independent protein sequences into shared
token blocks saves padding, and that a block-diagonal attention mask is what
makes the trick *safe*. This lab checks both halves against a real checkpoint:
`facebook/esm2_t6_8M_UR50D`, the same 8M-parameter ESM-2 used in the protein
folding track. About 30 MB downloads on the first run.

The property to prove is simple to state and easy to get wrong:

> The per-residue embeddings of a sequence are the same whether that sequence
> is processed alone or packed alongside others.

If the mask leaks, packed embeddings are not a faster version of independent
inference — they are a different, silently corrupted computation. The negative
control in this lab measures that corruption at 23% to 64% relative error, so
it is not a rounding issue.

Everything graded runs on CPU in float32 under `torch.manual_seed(0)`. Absolute
embedding values never reach stdout: they would pin the grader to one
checkpoint revision and one `transformers` version. stdout carries integers,
shapes, `allclose` booleans, and packing percentages. Wall-clock timing and
raw difference magnitudes go to **stderr**.

## Part 1 — Packing real tokenized lengths

The fourteen sequences are real peptides and small proteins, listed in arrival
order. Tokenize them with the ESM-2 tokenizer. Each sequence occupies
`residues + 2` tokens because of `<cls>` and `<eos>` — 444 residues become 472
tokens, which is 28 slots the packing heuristic has to budget for and that a
length-from-the-FASTA-header estimate would miss.

Implement `padded_slots` (naive batching in arrival order, batch size 4) and
`first_fit_decreasing`. Also run the naive counter on length-sorted input, which
is the "just bucket by length" baseline operators actually try before packing.
Report useful tokens, padded slots, waste, and per-pack occupancy.

First-fit decreasing is a heuristic, not an algorithm. Bin packing is NP-hard;
FFD is known to use at most $\frac{11}{9}\,\mathrm{OPT} + 1$ bins. The lab does
not ask you to prove that bound, but it is why the packed layout is allowed to
be slightly imperfect and still counted as a win.

## Part 2 — Isolation, and what HuggingFace ESM actually accepts

A 2D `attention_mask` of shape `(batch, seq)` expresses padding. It cannot
express "these tokens belong to different sequences." You need a per-pair mask.

HuggingFace's `EsmModel.forward` will not take one. It rejects a 4D mask
outright and crashes on a 3D one, because the embedding layer reuses the same
tensor as a per-token padding mask. The starter therefore splits the work:

- the 2D padding mask goes to `model.embeddings`;
- a 4D *additive* block-diagonal mask (`0` on allowed pairs, `-inf` on the
  rest) goes straight to `model.encoder`.

You implement `block_diagonal_keep_mask`, `to_additive`, and the packing of
`input_ids`. `encode_packed` is given, because the bypass is an API workaround
rather than the learning objective.

Then run three comparisons, all against the same standalone per-sequence
forward passes:

1. **Padded batching.** A rectangular batch with a standard 2D padding mask
   should match standalone. This is the related production bug class: getting
   the padding mask wrong silently changes embeddings, and it is worth proving
   the well-behaved path before the packed one.
2. **Packed, block-diagonal.** Each segment sliced out of the packed output
   should `allclose` its standalone reference.
3. **Packed, padding-only mask (negative control).** The same packed batch,
   but every real token may attend to every other real token in its pack.
   Nothing should match. Report the worst and least relative corruption.

A correctness test that cannot fail proves nothing. The negative control is
the most memorable number in the module.

## Part 2c — Position IDs, which ESM-2 happens not to need

ESM-2 uses *rotary* position embeddings. Rotary attention depends on $i - j$,
so a constant offset on a packed segment cancels in every query-key pair
inside that segment. Packed ESM-2 embeddings match standalone even if position
IDs run continuously across the pack.

That is a property of *this* architecture, not of packing in general. BERT,
T5, and many folding trunks use learned absolute positions, and for those a
continuous `position_ids` tensor silently shifts every embedding. The lab
demonstrates this on a tiny attention block you fully control: the same packed
tokens, the same block-diagonal mask, and two position tensors. Per-segment
IDs match standalone 14 of 14. Continuous IDs match only the 4 segments that
happen to sit at offset 0; the other 10 corrupt by up to 144%.

If you ever pack a model and skip this check because "ESM didn't need it,"
that is the bug.

## Part 3 — What packing costs

Attention is quadratic in the *packed* length, not in the useful length. A
dense kernel over a pack of capacity 128 scores $128^2$ pairs even when the
block-diagonal mask would have allowed only the per-segment squares. Report
both. In this workload the packed dense kernel does **more** attention work
than naive padded batching (`65536` vs `48528` score entries, `1.35x`). Packing
saves memory traffic on the sequence axis and saves work only if the kernel
can skip masked blocks.

The mask itself is quadratic in pack capacity. At this lab's size it is
256 KiB. The same layout at capacity 8192 with 8 packs is 2 GiB in float32.
That is why production packing often stores a bool mask, a compressed block
index, or relies on a kernel that never materializes the mask at all.

Do not change the starter constants or the output labels. The grader checks
printed stdout.

## Recap

You packed real protein sequences, proved against ESM-2 8M that a
block-diagonal mask makes the packed batch identical to independent inference,
measured what a missing mask actually does, and quantified the quadratic-work
caveat that a padding-waste percentage conceals. The next module is a quiz
over serving and biology; it will ask you when packing is safe and when it is
not.
