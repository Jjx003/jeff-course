# Implement groupwise INT4 quantization

In this exercise you will implement the smallest useful version of weight
quantization: symmetric groupwise INT4. The point is not to build a production
quantizer. The point is to make the data structure visible.

Low-bit weights are not just tiny integers. They are tiny integers plus enough
metadata to reconstruct approximate real values. In this module, the metadata
is one scale per group.

Given the weight vector in the starter code:

1. Split it into groups of 4.
2. For each group, compute:

$$
s = \frac{\max |x|}{7}
$$

3. Quantize each value:

$$
q = \operatorname{clip}(\operatorname{round}(x/s), -7, 7)
$$

4. Dequantize with:

$$
\hat{x} = qs
$$

5. Print group scales, quantized values, dequantized values, and mean absolute
   error.

Do not change the starter constants or output labels. The grader checks the
printed values.

## Why the range is -7 to 7

Signed 4-bit integers can represent 16 code points. Many symmetric quantizers
use a range like `[-7, 7]` rather than `[-8, 7]` because it keeps the positive
and negative sides balanced around zero. That leaves one code point unused, but
it simplifies the scale convention and avoids giving the negative side one
extra level.

The scale maps the largest absolute value in the group to magnitude 7:

$$
\max_i |x_i| \mapsto 7
$$

Every other value in the group lands on the nearest integer grid point.

## Worked example

For the group:

```text
[-1.2, -0.8, -0.1, 0.0]
```

the scale is:

$$
s = 1.2 / 7 \approx 0.171429
$$

Then:

| Value | Value / scale | Rounded | Dequantized |
|---:|---:|---:|---:|
| -1.2 | -7.00 | -7 | -1.200 |
| -0.8 | -4.67 | -5 | -0.857 |
| -0.1 | -0.58 | -1 | -0.171 |
| 0.0 | 0.00 | 0 | 0.000 |

The largest value reconstructs exactly because it defined the scale. The
others move to nearby grid points. That movement is quantization error.

## What this leaves out

Production quantizers add many details this exercise omits:

- packing two 4-bit values into one byte;
- vectorized dequantization kernels;
- group sizes like 32, 64, or 128;
- per-channel or per-block scales;
- zero points for asymmetric ranges;
- calibration data;
- outlier handling;
- mixed precision for fragile layers.

Those details matter, but they build on the same mechanism: choose a scale,
round to low-bit codes, store metadata, and reconstruct approximately.

## Recap

After this exercise, groupwise INT4 should feel less like a buzzword and more
like a concrete representation. The next quiz checks whether you can separate
weight quantization, activation quantization, KV-cache compression, and QLoRA's
adapter-based memory plan.
