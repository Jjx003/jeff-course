# Roofline lower bounds

A roofline model compares the work an operation must do with the bytes it must
move. The simplest version gives two lower bounds:

$$
t_\text{memory} = \frac{\text{bytes moved}}{\text{memory bandwidth}}
$$

$$
t_\text{compute} = \frac{\text{FLOPs}}{\text{peak FLOPs}}
$$

The real runtime must be at least the larger of those two values. In practice
it will be larger because kernels are not perfect, memory access is not always
coalesced, Tensor Cores are not always full, and scheduling adds overhead. But
the larger lower bound often tells you which class of optimization is worth
thinking about first.

## Arithmetic intensity

The bridge between memory and compute is arithmetic intensity:

$$
I = \frac{\text{FLOPs}}{\text{bytes moved}}
$$

An operation with high arithmetic intensity does many computations for each
byte loaded. Large matrix multiplication during prefill can have high
intensity because many prompt tokens are processed together. An operation with
low intensity does little work for each byte loaded. Small-batch decode often
has lower intensity because the model repeatedly streams weight matrices for
one or a few new tokens.

The boundary between memory-bound and compute-bound depends on the machine:

$$
I_\text{ridge} = \frac{\text{peak FLOPs/s}}{\text{bandwidth bytes/s}}
$$

If your operation's intensity is below this ridge point, memory bandwidth is
the likely limiter. If it is above, compute throughput may become the limiter.

## Why decode is often memory-bound

For a decoder-only transformer, a new token passes through every layer. The
rough matmul cost is commonly estimated as:

$$
F \approx 2P
$$

where $P$ is the number of parameters. The factor of 2 comes from multiply-add
work. A 70B model therefore has about 140 GFLOP of matmul work per generated
token.

In BF16, the raw weight storage is:

$$
70 \times 10^9 \times 2 = 140 \times 10^9 \text{ bytes}
$$

If there is little batch reuse, reading those weights can dominate. Weight-only
quantization attacks exactly this term: INT8 roughly halves the bytes, INT4
roughly quarters them before metadata, and specialized formats add their own
scales or codebooks.

## Why prefill can behave differently

Prefill processes the prompt tokens together. Instead of multiplying a weight
matrix by one hidden vector, the system multiplies by a taller matrix of token
states. That reuses each loaded weight across many token positions and raises
arithmetic intensity. This is one reason long prompts can have high throughput
in tokens per second while interactive decode still feels latency-sensitive.

The distinction matters when reading benchmarks. A vendor chart might report
excellent throughput for long-sequence prefill. That does not automatically
mean a single-user streaming chat workload improves by the same factor.

## KV cache capacity

The KV cache is a second memory story. It is not fixed by parameter count. It
grows with active requests and context length:

$$
\text{KV bytes} =
L \times T \times H_\text{kv} \times D \times 2 \times b
$$

where:

- $L$ is number of layers,
- $T$ is context length,
- $H_\text{kv}$ is KV heads,
- $D$ is head dimension,
- the factor of 2 stores keys and values,
- $b$ is bytes per stored value.

Grouped-query attention reduces $H_\text{kv}$. KV-cache quantization reduces
$b$. Paged attention reduces fragmentation and makes allocation more flexible.
These are different levers for the same pressure point.

## A worked interpretation

Suppose your estimate says:

| Quantity | Meaning |
|---|---|
| weight read: 140 GB | raw BF16 model bytes |
| matmul work: 140 GFLOP | approximate work for one token |
| memory lower bound: tens of ms | floor from bandwidth |
| compute lower bound: fractions of ms | floor from peak BF16 |

The immediate conclusion is not "the model will take exactly tens of
milliseconds per token." The conclusion is "for this simplified small-batch
decode model, reducing bytes or increasing reuse is probably more valuable than
chasing more peak FLOP/s."

That explains why quantization, batching, speculative decoding, and kernel
fusion all show up in inference systems. They attack different missing pieces:
fewer bytes, more reuse, fewer expensive target-model steps, or less overhead
around the math.

## Practical caveats

This exercise ignores several terms that matter in production:

- reading and writing the KV cache during attention;
- output projection and sampling;
- CPU scheduling and request bookkeeping;
- tensor-parallel or pipeline-parallel communication;
- memory fragmentation;
- adapter application;
- safety filters or tool-use orchestration around the model.

The simplification is still useful. A clean lower bound is the first line of
defense against magical thinking. You can add missing terms later, but you
should first know whether the giant obvious term already explains the behavior.

## Connection to the next modules

The next two modules focus on quantization. Once you see a 140 GB weight-read
term, weight-only INT4 is no longer an abstract compression trick. It is a way
to reduce the dominant byte movement in a particular decode regime. The module
after that asks you to implement the smallest possible version of this idea:
store low-bit integers plus scales, then reconstruct approximate weights.
