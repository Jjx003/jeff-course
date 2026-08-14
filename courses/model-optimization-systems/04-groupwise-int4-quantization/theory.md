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

| Group size | Scale overhead/value | Int payload/value | Total bits/value |
|---:|---:|---:|---:|
| 4 | 4.00 bits | 4 bits | 8.00 bits |
| 32 | 0.50 bits | 4 bits | 4.50 bits |
| 64 | 0.25 bits | 4 bits | 4.25 bits |
| 128 | 0.125 bits | 4 bits | 4.125 bits |
| 512 | 0.031 bits | 4 bits | 4.031 bits |

Group size 4 is included only to show how badly metadata dominates at the
extreme: a 4-bit payload with a 16-bit scale every four values is no smaller
than fp8. Production formats cluster in the 32-to-128 range, and the exercise
computes this same column directly from byte counts rather than trusting the
table.

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

The practical consequence is which error you report. Weight MAE is a property of
a tensor sitting in memory. What a user experiences is the layer's output, so the
more honest measure is relative output error on a real activation batch:

$$
\frac{\lVert x\hat{W}^{\top} - xW^{\top} \rVert_F}{\lVert xW^{\top} \rVert_F}
$$

These two can disagree. Quantization error that happens to land in directions
the activations rarely excite costs almost nothing at the output, which is the
entire premise of activation-aware methods.

## Why group size matters only sometimes

Groupwise scaling is usually justified with the phrase "it handles outliers,"
which is true but incomplete. It is worth being precise about when a small group
size earns its metadata.

Consider a group whose values are all roughly the same magnitude. The scale is
set by the group maximum, every value lands on a reasonably fine grid, and the
quantization error per value is about $s/2 = \max|x| / 14$. Splitting that group
in half barely changes any local maximum, so it barely changes the error. For
weights drawn from a single Gaussian, this is the regime you are in: group size
is nearly irrelevant, and per-tensor scaling is the correct engineering choice.

Now suppose one value in the group is 25 times larger than the rest. The scale is
set by that one value, so the grid spacing becomes 25 times coarser for every
other member of the group. Ordinary weights that would have quantized cleanly get
crushed toward zero. The damage is proportional to how many values share a group
with the spike, which is exactly $G - 1$.

So the value of a small group size is not a fixed property of INT4. It is a
function of how heavy-tailed the weight distribution is:

| Weight distribution | Effect of halving $G$ | Is the metadata worth it? |
|---|---|---|
| Near-Gaussian, no spikes | Negligible error change | No — use large groups |
| Occasional large outliers | Error falls substantially | Yes |
| Many outliers per row | Small groups help, but consider keeping outliers in higher precision | Partially |

Trained transformers reliably fall into the second and third rows. Specific
feature dimensions develop activations and weights far outside the typical range,
and those channels persist across inputs rather than moving around. That
persistence is what makes the problem tractable: because the outlier channels are
stable, a quantizer can find them once during calibration and protect them.

This also explains a confusing pattern in practice. Two engineers can both
report honestly that "INT4 worked fine" and "INT4 wrecked the model," and both be
correct, because they quantized different weight distributions at different group
sizes. The compression ratio alone does not tell you which regime you are in —
you have to measure the output error.

## Packing versus math

Packing is a storage operation, and it is easy to under-rate. An `int8` tensor
holding values in `[-7, 7]` is already a valid set of INT4 codes mathematically,
yet it saves nothing over INT8 because each code still occupies a full byte. The
format only becomes four bits per weight when two codes share a byte, which is
why the exercise packs into `uint8` and verifies the round-trip exactly.

The standard trick is a bias. Codes live in `[-7, 7]`, so adding 8 maps them to
`[1, 15]`, which fits in an unsigned nibble and avoids sign-extension entirely.
Without the bias, a right shift on a signed type propagates the sign bit and
corrupts the high nibble of every negative byte.

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

Groupwise INT4 exposes four core ideas that reappear everywhere:

1. Low-bit formats need metadata, and the metadata belongs in the byte count.
2. Local scaling fights outliers — but only when there are outliers to fight.
3. Compression and speed are not identical.
4. The error that matters is measured at the output, not on the weight.

Those ideas also apply to NF4, FP8 calibration, KV-cache quantization, and
adapter initialization methods that compensate for quantization error.

## Transition

The next module is a checkpoint. It asks you to sort optimization claims by the
tensor being compressed and the bottleneck being targeted. The mechanics you just
implemented are simple — a reshape, a division, a round, and some bit shifting.
The engineering judgment comes from knowing which tensor to point them at, and
the exercise's two sweep tables are the first concrete evidence that the same
format can be either free or ruinous depending on what you apply it to.
