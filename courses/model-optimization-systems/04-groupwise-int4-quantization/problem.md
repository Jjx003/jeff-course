# Implement groupwise INT4 quantization

The reading module argued that a low-bit format is integer codes *plus* enough
metadata to reconstruct approximate real values. Now you will build one against
a real weight matrix and check whether the argument survives contact with data.

You will quantize the weight of a `torch.nn.Linear(512, 256, bias=False)` — 131,072
real parameters, not a hand-written list. By the end you will have answered three
questions with measurements rather than assertions:

1. Does the packed format round-trip exactly?
2. What does the format actually cost, in bytes, including metadata?
3. What does a smaller group size buy you — and when does it buy you nothing?

Everything runs on CPU in float32. That is deliberate: quantization is a
numerics exercise, and a fixed device plus a fixed seed means your numbers match
the grader's exactly.

## Part 1 — Quantize and dequantize

Implement `quantize_groupwise(weight, group_size)`. Groups run along the input
dimension, so a `(256, 512)` weight with group size 64 has 8 groups per output
row and `256 x 8 = 2048` scales in total.

For each group, with $Q_{\max} = 7$:

$$
s_g = \frac{\max_{i \in g} |x_i|}{Q_{\max}}, \qquad
q_i = \operatorname{clip}\!\left(\operatorname{round}\!\left(\frac{x_i}{s_g}\right), -Q_{\max}, Q_{\max}\right)
$$

Return `codes` as `torch.int8` in the weight's original shape, and `scales` as
`float32` with shape `(out_features, n_groups)`. Use a scale of `1.0` for any
all-zero group so you never divide by zero.

Then implement `dequantize_groupwise` to reconstruct $\hat{x}_i = q_i s_g$.

The reshape-to-groups trick is the whole technique: view the weight as
`(out_features, n_groups, group_size)` and every reduction over `dim=-1` becomes
a per-group reduction.

## Part 2 — Pack two codes per byte

This is the part the previous framing left out, and it is where "4-bit" stops
being a figure of speech.

`torch.int8` codes still occupy one byte each, so `codes` alone saves nothing
over INT8. Implement `pack_int4` to place two codes in every byte:

- shift the signed range `[-7, 7]` up by 8 into the nibble range `[1, 15]`;
- put even columns in the low nibble and odd columns in the high nibble;
- return a `torch.uint8` tensor of shape `(out_features, in_features // 2)`.

Then implement `unpack_int4` to invert it. Packing is only legitimate if it is
lossless, so the program asserts nothing and simply prints whether

```text
unpack_int4(pack_int4(codes)) == codes
```

holds exactly. That line must print `True`. Bit manipulation either round-trips
or it does not — there is no "close enough" here.

Use `torch.bitwise_or`, `torch.bitwise_and`, `torch.bitwise_left_shift`, and
`torch.bitwise_right_shift`. Note that `>>` on a signed dtype propagates the
sign bit, which is exactly the bug the `+8` bias exists to avoid.

## Part 3 — Count the bytes honestly

Implement `int4_bytes` returning `(payload_bytes, scale_bytes, total_bytes)`.
The payload holds two weights per byte; scales are fp16, one per group.

A format that ignores its own metadata is lying about its compression ratio, so
report `effective bits/weight` as `total_bytes * 8 / n_weights`. For group size
64 you should land on exactly `4.250` — the `4 + 16/64` from the theory table,
now computed rather than tabulated.

## Part 4 — What group size actually buys

Fill in the measurement loop in `sweep_table`. For each group size, report
`bits/weight`, the mean absolute error of the reconstructed weight, and the
relative error of the **layer output**:

$$
\text{out\_rel\_err} = \frac{\lVert x\hat{W}^{\top} - xW^{\top} \rVert_F}{\lVert xW^{\top} \rVert_F}
$$

The output error is the one that matters. Nobody deploys a weight matrix; they
deploy the function it computes.

The sweep runs twice. The first pass uses the layer's own Gaussian-initialized
weights. The second pass calls `inject_outliers`, which multiplies every 137th
column by 25 to imitate the outlier channels that real trained transformers
develop.

Compare the two tables before reading the tips. The gap between them is the
entire reason production quantizers use group sizes of 32 to 128 instead of one
scale per tensor, and it is not visible at all in the Gaussian case.

Do not change the starter constants or the output labels. The grader checks
printed stdout.

## Recap

You now have a groupwise INT4 quantizer that packs real bytes, reports its true
metadata cost, and measures error where it counts. The next module is a
checkpoint that asks you to sort optimization claims by which tensor is being
compressed and which bottleneck is being targeted.
