# Solution walkthrough

## Tokenization changes the instance

444 residues become 472 tokens. Every sequence pays two special tokens, and
those 28 slots are 6% of the useful budget. Packing from FASTA lengths would
have produced a different, illegal layout the moment a pack that "fit" in
residues overflowed in tokens. The rest of the lab is downstream of this
count.

## Three baselines, not one

Arrival-order padding wastes `40.4%`. Sorting by length first — the thing
everyone tries before they write a packer — wastes `22.6%`. FFD at capacity
128 wastes `7.8%` across four packs, three of which are above 98% occupancy.
The fourth pack holds the leftover peptides and is only 72% full; that is the
FFD tail, not a bug. Slots saved versus naive: `35.4%`. Versus bucketing:
`16.1%`. The second number is the honest win over the obvious alternative.

## HuggingFace ESM will not take a 4D mask

`EsmModel.forward` rejects a 4D `attention_mask` and mis-indexes a 3D one
because `EsmEmbeddings` reuses the tensor as a per-token pad indicator. The
bypass is mechanical: 2D pad mask into `embeddings`, 4D additive mask into
`encoder`. Once that is in place, packed embeddings match standalone for all
14 sequences to within `1e-5`. Padded rectangular batching matches too. Both
results are self-consistency checks against the same weights, which is why
they are safe to grade across library versions.

## The negative control is the point

The same packed `input_ids`, the same weights, and a padding-only mask —
every real token attends to every other real token in its pack — matches
**0 of 14** standalone references. Worst relative error `64%`, least `23%`,
and every sequence is above 1%. Cross-contamination is not a rounding error.
A retrieval index, a variant-effect probe, or a fine-tune built on these
embeddings would be measuring a packed-batch artifact.

This is also why the test has teeth. A packed implementation that accidentally
used the 2D mask would fail here, and would have looked fine on occupancy
percentages.

## Rotary embeddings hide a second bug class

ESM-2's rotary positions depend on $i - j$, so a constant segment offset
cancels. Packed ESM-2 therefore matches standalone *without* resetting
position IDs. The toy block, which uses learned absolute positions, does not:
per-segment IDs match 14 of 14, continuous IDs match only the 4 segments at
offset 0, and the other 10 corrupt by up to 144%. The two results together
are the lesson. Packing ESM-2 without resetting IDs is correct; packing a
BERT-style trunk the same way is not. The architecture, not the packer,
decides.

## Dense packing can cost attention FLOPs

Score entries, one per query-key pair per head per layer:

| Layout | Entries |
|---|---:|
| naive padded | 48,528 |
| length-bucketed | 34,438 |
| packed, dense kernel | 65,536 |
| packed, block-sparse / one-at-a-time | 20,966 |

The packed dense kernel does `1.35x` more attention work than naive padding
and `3.13x` more than a kernel that skipped masked blocks. Packing still
reduces sequence-axis memory traffic and kernel launches (4 forwards instead
of 14), which is often the actual win on a small model. It is not free
compute, and a waste-percentage that ignores quadratic attention is an
incomplete argument.

The mask tensor's own footprint makes the same point at larger capacity: 256
KiB here, 2 GiB at capacity 8192 with 8 packs, in float32. Bool storage or a
segment-offset list is not a micro-optimization at that size; it is what
makes the layout deployable.

## What this still leaves out

The lab packs independent sequences for a protein language model. It does not
pack:

- MSAs, where row and column attention have their own isolation rules;
- pair representations, which are quadratic in the *unpacked* residue count
  and do not become cheaper because the 1D tokens share a buffer;
- complexes, where "do not attend across chains" is sometimes the opposite
  of what you want.

The right generalization is the one the recap already stated: pack
independent sequence workloads once both contracts have been checked against
the actual model; pack structure workloads only when the model says so.
