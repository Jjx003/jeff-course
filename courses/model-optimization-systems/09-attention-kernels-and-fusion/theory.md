# Online softmax recurrence

The key mathematical trick behind tiled exact attention is that softmax can be updated block by block without storing all scores at once.

For a row of attention scores $x_1,\dots,x_n$, the stable softmax denominator is:

$$
l = \sum_i e^{x_i-m}
$$

where:

$$
m = \max_i x_i
$$

Now suppose the row arrives in blocks. For the old blocks, keep:

$$
m_\text{old} = \max_{i \in \text{old}} x_i
$$

$$
l_\text{old} = \sum_{i \in \text{old}} e^{x_i-m_\text{old}}
$$

For a new block $b$, compute:

$$
m_b = \max_{j \in b} x_j
$$

$$
l_b = \sum_{j \in b} e^{x_j-m_b}
$$

The combined maximum is:

$$
m_\text{new} = \max(m_\text{old}, m_b)
$$

The combined denominator is:

$$
l_\text{new} =
e^{m_\text{old}-m_\text{new}}l_\text{old}
+ e^{m_b-m_\text{new}}l_b
$$

The exponentials rescale both partial sums into the same reference frame. This is the whole numerical stability story: every block may have used its own maximum, but the merged denominator is as if all scores had been normalized by the final maximum.

## Including values

Attention is not just softmax probabilities. It is a weighted sum of value vectors:

$$
o = \sum_i p_i v_i
$$

where:

$$
p_i = \frac{e^{x_i-m}}{l}
$$

It is usually easier to maintain an unnormalized numerator:

$$
n = \sum_i e^{x_i-m}v_i
$$

Then:

$$
o = \frac{n}{l}
$$

When a new block arrives, compute its block numerator:

$$
n_b = \sum_{j \in b} e^{x_j-m_b}v_j
$$

and merge:

$$
n_\text{new} =
e^{m_\text{old}-m_\text{new}}n_\text{old}
+ e^{m_b-m_\text{new}}n_b
$$

Finally:

$$
o_\text{new} = \frac{n_\text{new}}{l_\text{new}}
$$

The next coding lab asks you to implement exactly this one-row version.

## Prefill versus decode

LLM inference has two very different phases:

| Phase | What happens | Common bottleneck |
|---|---|---|
| Prefill | Process the prompt tokens, often many at once | Attention/MLP throughput and long-context memory traffic |
| Decode | Generate one or a few new tokens per request | KV-cache reads, scheduling, memory bandwidth |

FlashAttention-style kernels are especially visible during prefill because many prompt tokens attend over many previous prompt tokens. During decode, each request often contributes one new query token, so the computation shape changes. Decode performance depends heavily on KV-cache layout, batching, and how efficiently the system reads old keys and values.

This distinction is why serving benchmarks report time-to-first-token and output tokens per second separately. A change that improves prefill may not improve decode, and vice versa.

## Layout and precision

Fast kernels care about details that high-level equations ignore:

- head dimension,
- number of query heads versus KV heads,
- causal versus bidirectional masks,
- packed versus padded batches,
- tensor memory layout,
- dtype of Q, K, V, and output,
- whether dropout is needed,
- whether rotary embeddings are fused,
- whether quantized values must be dequantized inside the kernel.

In training, backward pass support also matters. In inference, the key questions are usually latency, throughput, memory footprint, and numerical tolerance. FP8 and low-bit paths can be excellent on the right hardware, but they need calibration and careful validation on the actual model and task.

## Practical caveats

Kernel claims are easy to overgeneralize. Keep these distinctions clear:

- Exact tiled attention changes memory traffic, not the mathematical attention result.
- Approximate or sparse attention changes the computation itself.
- Weight quantization reduces model storage and matmul bandwidth, but it does not automatically reduce KV-cache memory.
- KV-cache quantization reduces serving memory, but it can affect long-context retrieval quality.
- Fusion can make one path fast while making unusual shapes harder to support.

## Going deeper

- FlashAttention paper: https://arxiv.org/abs/2205.14135
- FlashAttention-2 paper: https://arxiv.org/abs/2307.08691
- FlashAttention-3 paper: https://arxiv.org/abs/2407.08608
- FlashAttention repository: https://github.com/Dao-AILab/flash-attention
- TensorRT-LLM attention documentation: https://nvidia.github.io/TensorRT-LLM/advanced/gpt-attention.html
