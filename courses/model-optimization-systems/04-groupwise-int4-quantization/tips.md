# Hints

Implement the helper functions directly. There is no need for NumPy.

For `quantize_group`:

1. Compute `max_abs = max(abs(x) for x in group)`.
2. Use `scale = max_abs / 7` unless `max_abs == 0`.
3. For an all-zero group, use `scale = 1.0` to avoid division by zero.
4. For each value, compute `round(x / scale)`.
5. Clamp the rounded value between `-7` and `7`.
6. Return the scale and integer list.

For `dequantize_group`, multiply each integer by the scale.

## Common mistakes

- Dividing by 8 instead of 7.
- Forgetting to clamp after rounding.
- Returning floats for quantized values instead of integers.
- Computing one global scale for all weights instead of one scale per group.
- Rounding printed values manually instead of letting the starter formatting do
  it.
- Forgetting that `chunks` already yields the right group slices.

## Sanity checks

The first group has maximum absolute value `1.2`, so its scale should be
approximately `0.171429`. The first quantized value should be `-7` because
`-1.2` defines the range. The restored first value should be exactly `-1.2`
after rounding in the printout.

The final group has a much larger range because of `3.1` and `-3.4`, so its
small values are likely to reconstruct poorly. That is the outlier story in
miniature.

## Going deeper

After the solution passes, try changing `GROUP_SIZE` privately:

- Group size 1 reconstructs every nonzero value exactly with a scale per value,
  but the metadata cost is absurd.
- Group size 12 uses one scale for the whole vector, reducing metadata but
  increasing error.
- Group size 4 sits in the middle for this toy example.

This is the same tradeoff production quantizers make with much larger tensors.
