# Scales, zero points, and error

Uniform affine quantization maps real numbers into integers:

$$
q = \operatorname{clip}\left(\operatorname{round}(x/s + z), q_\min, q_\max\right)
$$

and reconstructs with:

$$
\hat{x} = s(q - z)
$$

Here $s$ is the scale and $z$ is the zero point. Symmetric quantization sets
$z=0$ and uses a signed integer range. It is common for weights because it is
simple and hardware-friendly. Asymmetric quantization uses a nonzero zero point
to represent shifted ranges more efficiently, often useful for activations.

## Quantization error

Quantization error is:

$$
e_i = x_i - \hat{x}_i
$$

Common summaries include mean absolute error:

$$
\text{MAE} = \frac{1}{n}\sum_i |x_i - \hat{x}_i|
$$

and mean squared error:

$$
\text{MSE} = \frac{1}{n}\sum_i (x_i - \hat{x}_i)^2
$$

Those summaries are useful but incomplete. A small average error in an
unimportant layer may not matter, while a small-looking error in a sensitive
projection can damage downstream quality. Calibration methods exist because
"minimize local reconstruction error" is not always the same as "preserve model
behavior."

## Why group size matters

Groupwise quantization splits a tensor into groups and stores one scale per
group. If a group has $G$ values and each value is stored in 4 bits, the raw
integer payload costs:

$$
4G \text{ bits}
$$

If each group stores a 16-bit scale, the effective cost per value is:

$$
4 + \frac{16}{G} \text{ bits}
$$

That means:

| Group size | Payload bits/value | Scale overhead/value | Total before packing details |
|---|---:|---:|---:|
| 32 | 4 | 0.50 | 4.50 |
| 64 | 4 | 0.25 | 4.25 |
| 128 | 4 | 0.125 | 4.125 |

Small groups adapt better to local ranges but store more metadata. Large groups
have less overhead but more error from outliers. Production formats add packing
constraints, alignment, per-channel scales, codebooks, or nested quantization
of the scales themselves.

## Outliers

Transformer activations and some weight channels contain outliers. A single
large value can force a wide scale, wasting most quantization levels on empty
space. For example, if a group contains:

```text
[0.04, 0.02, -0.03, 5.00]
```

a symmetric scale must cover 5.00. The three small values may all round to
zero. If those small values are important, quality suffers.

This is why practical methods add structure:

- per-channel scaling gives each output channel its own range;
- groupwise scaling localizes outliers;
- activation-aware methods protect channels that matter for real data;
- mixed precision leaves fragile tensors in higher precision;
- SmoothQuant-style methods redistribute scale between weights and activations.

## INT4 versus NF4

Uniform INT4 places levels evenly. NF4 uses a learned or designed codebook
suited to normally distributed weights. The difference is easiest to describe
geometrically:

| Format | Level placement | Good fit |
|---|---|---|
| INT4 | evenly spaced after scaling | simple hardware-friendly ranges |
| NF4 | denser near common normal values | frozen pretrained weights in QLoRA |

NF4 still needs scales and dequantization. It is not magic; it is a better
allocation of 16 code points for a common weight distribution.

## Weight-only versus weight-activation quantization

Weight-only quantization stores weights in low-bit form and dequantizes them
during computation, often accumulating in FP16/BF16/FP32. It mainly reduces
model storage and weight bandwidth. It is attractive for decode when reading
weights dominates.

Weight-activation quantization uses low-bit activations too. This can unlock
faster low-bit matmuls on supported hardware, but it is harder because
activation ranges depend on inputs. Calibration must see representative data,
and online scaling may add overhead.

## KV cache is its own problem

KV-cache quantization has a different lifecycle. Weights are fixed after model
loading. KV entries are produced during each request. That makes cache
quantization both attractive and delicate:

- attractive because long context and many users create huge cache pressure;
- delicate because quantization happens on the serving path;
- workload-dependent because prompt distributions affect ranges;
- quality-sensitive because attention repeatedly uses cached values.

Some systems quantize only older cache blocks, some quantize per head or per
token block, and some keep special tokens or layers at higher precision. The
right design depends on latency, context length, and accuracy tolerance.

## Accuracy is workload-specific

A chat benchmark, a code benchmark, a long-context retrieval benchmark, and a
protein variant-effect benchmark may react differently to the same bit width.
Treat quantization as an engineering experiment, not a universal truth.

Useful evaluation pairs include:

| Deployment goal | Quality check |
|---|---|
| chat serving | preference, safety, refusal, tool-use behavior |
| code generation | unit tests, pass@k, repository-level tasks |
| retrieval over long context | needle retrieval, citation accuracy |
| protein embeddings | downstream classification or regression |
| folding pipeline | structure metrics and confidence calibration |

## Transition

The next module strips all of this down to the smallest useful mechanism:
split a vector into groups, choose a symmetric scale, store signed 4-bit
integers, reconstruct, and measure error. It is tiny, but it contains the core
tradeoff that larger quantizers elaborate.
