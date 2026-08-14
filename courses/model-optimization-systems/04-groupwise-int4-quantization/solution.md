# Solution walkthrough

## The reshape does the work

Almost all of the difficulty in groupwise quantization is index bookkeeping, and
a single reshape removes it. Viewing the weight as
`(out_features, n_groups, group_size)` turns "per-group maximum" into
`amax(dim=-1)`, and `keepdim=True` makes the subsequent division broadcast with
no further effort. This works only because groups are contiguous along the input
dimension; grouping along the output dimension would need a transpose first.

## Packing is the part that makes it INT4

Producing `int8` codes in `[-7, 7]` is quantization, not compression. Those codes
still take a byte each, so on their own they match INT8's footprint. The `+8`
bias into `[1, 15]` is what makes the nibble arithmetic safe: unsigned values
have no sign bit to propagate on a right shift.

`stack` followed by `reshape` is the exact inverse of the `0::2` / `1::2` split.
`cat` is the tempting wrong answer — it produces all even columns followed by all
odd columns, which is a permutation of the right answer and round-trips to
`False`. Because the check is `torch.equal` on integers, that bug cannot hide.

## Why the byte count includes scales

At group size 64 the format costs exactly `4 + 16/64 = 4.25` bits per weight, and
the program derives it from byte counts rather than restating the formula.
Reporting the payload alone would claim 4.000 bits per weight and a clean `4x`
compression, which is simply false — the scales are real bytes that must be
loaded to reconstruct anything.

The measured compression is `3.76x`, not `4x`. That gap is the metadata.

## The two sweeps are the actual lesson

The Gaussian table is nearly flat: output relative error moves from about
`0.0685` at group size 32 to `0.0714` at 512. Group size 32 costs `0.47` more
bits per weight than 512 and buys roughly a 4% error improvement. On this
distribution, per-tensor scaling is the correct call.

The outlier table moves from about `0.163` to `0.404` over the same range. Same
code, same bit budgets, completely different conclusion.

The mechanism is worth stating precisely: a group's scale is set by its largest
magnitude, so a single 25x column forces a 25x coarser grid on every other value
sharing that group. The number of values damaged by one spike is `G - 1`, which
is why the error grows roughly with group size once outliers are present.

This is the honest version of "INT4 works." It works when the weight
distribution is well behaved or the group size is small enough to quarantine the
spikes, and the only way to know which case you are in is to measure output
error rather than trust the compression ratio.

## Where real quantizers go from here

The exercise stops at round-to-nearest. Production methods improve on it in ways
that all build on this same machinery:

- GPTQ keeps the groupwise format but chooses codes to compensate for error
  already introduced in earlier columns, using second-order information.
- AWQ rescales channels before quantizing so that activation-important weights
  land on a finer grid.
- Keeping a small set of outlier channels in fp16 attacks the problem from the
  other side, removing the spikes instead of shrinking the groups.

Each of those is a refinement of the same three-part structure you implemented:
choose a scale, round to low-bit codes, store the metadata needed to come back.
