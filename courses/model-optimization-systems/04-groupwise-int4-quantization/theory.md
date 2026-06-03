# Why INT4 still needs metadata

Four-bit weights are not enough by themselves. If a model stores only integer
codes like:

```text
[-7, -5, -1, 0, 1, 4, 6, -7]
```

you do not know whether those values represent numbers near `[-1, 1]`, near
`[-10, 10]`, or near `[-0.01, 0.01]`. A scale gives the codes physical meaning.
For symmetric groupwise quantization:

$$
\hat{x}_i = q_i s_g
$$

where $s_g$ is the scale for group $g$.

## Group size tradeoff

Small groups reduce error because each scale adapts to a local range. Large
groups reduce metadata overhead. If each group stores a 16-bit scale, the scale
overhead per value is:

$$
\frac{16}{G} \text{ bits/value}
$$

where $G$ is group size.

| Group size | Scale overhead/value | Int payload/value | Total before packing details |
|---:|---:|---:|---:|
| 4 | 4.00 bits | 4 bits | 8.00 bits |
| 32 | 0.50 bits | 4 bits | 4.50 bits |
| 128 | 0.125 bits | 4 bits | 4.125 bits |

This exercise uses group size 4 so the arithmetic fits on the page. Production
formats usually use larger groups because scale overhead and memory alignment
matter.

## Rounding and clipping

The quantization rule has two separate operations:

$$
q = \operatorname{round}(x/s)
$$

then:

$$
q = \operatorname{clip}(q, -7, 7)
$$

Rounding moves a value to the nearest representable grid point. Clipping handles
values outside the representable range. In this exercise clipping rarely does
anything because the scale is chosen from the maximum absolute value in the
same group. In calibrated quantizers, clipping can be intentional: accepting a
small amount of saturation can give better resolution to the majority of
values.

## Error is not uniformly important

Mean absolute error is easy to compute:

$$
\text{MAE} = \frac{1}{n}\sum_i |x_i - \hat{x}_i|
$$

But a model's quality does not depend only on average reconstruction error.
Errors in a key projection may hurt long-context retrieval more than errors in
another matrix. Errors in a protein model's structure head may affect geometry
more than errors in an embedding layer. That is why real quantizers calibrate
against layer outputs, activations, or task metrics rather than only minimizing
local tensor error.

## Packing versus math

The exercise stores quantized values as Python integers, but an actual INT4
format packs two 4-bit values into one byte. Packing is a storage operation.
Matmul kernels then need an efficient way to load packed values, unpack or
dequantize them, multiply, and accumulate into a higher-precision accumulator.

The speedup depends on the whole path:

- fewer bytes read from memory;
- efficient packed layout;
- fast dequantization;
- hardware support for low-bit math or a good emulation strategy;
- enough batch or shape regularity to keep kernels busy.

If unpacking costs more than the saved memory traffic, the format may shrink
the model without improving latency.

## Why groupwise INT4 is a useful teaching point

Groupwise INT4 exposes three core ideas that reappear everywhere:

1. Low-bit formats need metadata.
2. Local scaling fights outliers.
3. Compression and speed are not identical.

Those ideas also apply to NF4, FP8 calibration, KV-cache quantization, and
adapter initialization methods that compensate for quantization error.

## Transition

The next module is a checkpoint. It asks you to sort optimization claims by the
tensor being compressed and the bottleneck being targeted. If this exercise
felt mechanical, good. The mechanics are simple. The engineering judgment comes
from knowing where to use them.
