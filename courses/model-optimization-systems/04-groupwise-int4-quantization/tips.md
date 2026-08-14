# Hints

Work in the order the TODOs are numbered. Parts 1 and 2 are independent of the
measurement code, so get `unpack round-trip exact: True` printing before you
touch the sweep.

## Reshaping into groups

Every per-group reduction becomes a reduction over the last axis once you view
the weight correctly:

```python
grouped = weight.reshape(out_features, n_groups, group_size)
max_abs = grouped.abs().amax(dim=-1, keepdim=True)   # (out, n_groups, 1)
```

Keeping `keepdim=True` is what lets `grouped / scales` broadcast without any
manual index arithmetic. Squeeze the trailing dimension only when you return
the scales, and remember to `unsqueeze(-1)` again inside
`dequantize_groupwise`.

`reshape` works here because groups are contiguous along the input dimension.
If you ever group along the output dimension instead, you need a transpose
first — the memory layout stops cooperating.

## The all-zero group

```python
scales = torch.where(max_abs > 0, max_abs / QMAX, torch.ones_like(max_abs))
```

Computing `max_abs / QMAX` unconditionally and patching it afterwards is fine
because the division happens before the select. Avoid a Python `if`: `max_abs`
is a tensor with one entry per group, and any given group may or may not be
zero.

## Packing nibbles

The `+8` bias exists so that every code becomes a small non-negative integer
before any bit manipulation:

```python
nibbles = (codes.to(torch.int16) + 8).to(torch.uint8)   # [-7, 7] -> [1, 15]
low, high = nibbles[:, 0::2], nibbles[:, 1::2]
packed = torch.bitwise_or(low, torch.bitwise_left_shift(high, 4))
```

Casting through `int16` first avoids overflow while the bias is being added.
Going straight from `int8` risks wrapping if you later widen the code range.

To unpack, mask and shift, subtract the bias, then interleave:

```python
interleaved = torch.stack([low, high], dim=-1)      # (out, in//2, 2)
codes = interleaved.reshape(packed.shape[0], -1)    # (out, in)
```

`stack` then `reshape` is the inverse of the `0::2` / `1::2` split. Trying to
rebuild the column order with `torch.cat` instead gives you all the even
columns followed by all the odd ones, which round-trips to `False`.

## Common mistakes

- Dividing by 8 instead of 7 when forming the scale.
- Returning float codes instead of `torch.int8`.
- Computing one global scale for the whole tensor rather than one per group.
- Forgetting `keepdim=True`, which breaks the broadcast in the division.
- Using `>>` on a signed tensor, where the sign bit propagates and the high
  nibble comes back wrong for negative bytes.
- Using `torch.cat` instead of `stack` + `reshape` when unpacking.
- Reporting compression as `2x` from the payload alone and ignoring the scales.
- Comparing `float` equality on the round-trip. Codes are integers, so
  `torch.equal` is exactly right; `allclose` would hide a real bug.

## Sanity checks

- `codes min/max` should be `-7 7`. If your maximum is `8`, you clipped with
  the wrong bound.
- `scales shape` should be `(256, 8)` for group size 64.
- `packed shape` should be `(256, 256)` — half the columns, same rows.
- `effective bits/weight` should be exactly `4.250` at group size 64, `4.500`
  at 32, and `4.125` at 128. These are `4 + 16/G`.
- In the Gaussian table, `out_rel_err` should be near `0.069` and should barely
  move across group sizes.

## Reading the two tables

This is the real payoff, so do not skip it.

With Gaussian weights, output error moves from roughly `0.0685` to `0.0714` as
the group size goes from 32 to 512 — a change of about 4%. Paying 0.47 extra
bits per weight for group size 32 buys you almost nothing. If all weights were
Gaussian, per-tensor scaling would be the right engineering choice.

With outliers injected, the same sweep moves from roughly `0.163` to `0.404`.
Now group size is worth more than a factor of two in output error, and the extra
metadata is obviously worth paying for.

The mechanism: one 25x column inside a group inflates that group's `max_abs`,
so the scale grows, and every ordinary weight sharing the group gets rounded to
a coarser grid. Small groups quarantine the damage to a handful of values. Large
groups let a single outlier degrade hundreds of neighbours.

This is why "INT4 works fine" and "INT4 destroys my model" are both common
reports. The answer depends on the weight distribution and the group size, and
you cannot tell which regime you are in from the compression ratio alone.

## Going deeper

Things worth trying after the grader passes:

- Set `OUTLIER_MAGNITUDE` to `1.0` and watch the two tables converge, which
  confirms outliers are the only thing driving the gap.
- Add an asymmetric variant with a zero point, `q = round((x - min) / s)`, and
  see whether it helps on the outlier weights. It mostly does not — asymmetry
  addresses skew, not magnitude spikes.
- Store scales in fp32 instead of fp16 and recompute `bits/weight`. At group
  size 128 the metadata cost doubles from 0.125 to 0.25 bits per weight, which
  is why real formats keep scales small.
- Try clipping the scale below the group maximum, accepting saturation on the
  outlier to give the majority a finer grid. This is the core idea behind
  calibrated clipping thresholds.

## References

- Dettmers et al., *LLM.int8(): 8-bit Matrix Multiplication for Transformers at
  Scale* (2022) — the paper that made outlier channels famous.
- Frantar et al., *GPTQ: Accurate Post-Training Quantization for Generative
  Pre-trained Transformers* (2023) — groupwise INT4 with second-order error
  compensation.
- Lin et al., *AWQ: Activation-aware Weight Quantization* (2023) — chooses what
  to protect based on activations rather than weight magnitude.
