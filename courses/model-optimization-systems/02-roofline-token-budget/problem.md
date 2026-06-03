# Roofline math for token budgets

In the previous module, you saw the main budgets in modern model serving:
weight bandwidth, compute throughput, activation memory, KV cache capacity,
kernel overhead, and scheduling. This exercise makes the first two concrete.
You will write a tiny estimator for one decode step of a large decoder-only
LLM, then compare that with the KV-cache footprint of one long-context request.

This is deliberately a back-of-the-envelope program. It ignores embedding
lookups, logits projection details, non-matmul kernels, cache reads, launch
overhead, tensor parallel communication, and batching. That is fine. The point
is to learn what a lower bound feels like before adding complications.

Your program should print:

1. BF16 weight bytes for a 70B parameter model.
2. Approximate matmul FLOPs for one generated token.
3. Memory and compute lower bounds on an H100-like GPU.
4. KV-cache size for one 8192-token request with grouped-query attention.
5. KV-cache size for the same model with full multi-head KV storage.

Use decimal GB for weight bandwidth and GiB for cache capacity. The labels in
the output must match the starter comments because the grader compares the
printed lines.

## Constants

- Parameters: 70B
- Weight dtype: BF16, 2 bytes
- Approximate decode matmul FLOPs: $2 \times$ parameter count
- Memory bandwidth: 3350 GB/s
- Peak BF16 compute: 989 TFLOP/s
- Layers: 80
- GQA KV heads: 8
- MHA KV heads: 64
- Head dimension: 128
- Context length: 8192
- KV dtype: BF16, 2 bytes

## Why this exercise matters

A beginner might look at a 70B model and assume the dominant cost is the number
of floating-point operations. The roofline calculation shows a different
possibility. A single generated token has roughly:

$$
2 \times 70 \times 10^9 = 140 \times 10^9
$$

matmul FLOPs. That sounds huge, but modern accelerators have enormous peak
BF16 throughput. The same token also requires reading a very large amount of
weight data if there is little reuse across the batch.

The memory lower bound is:

$$
t_\text{memory} = \frac{\text{weight bytes}}{\text{bandwidth}}
$$

The compute lower bound is:

$$
t_\text{compute} = \frac{\text{FLOPs}}{\text{peak FLOPs}}
$$

If the memory lower bound is much larger, your first bottleneck guess is
memory. That does not mean compute is free. It means that even a perfect
implementation cannot beat the time required to move the bytes.

## KV cache formula

For this exercise, use:

$$
\text{KV bytes} =
\text{layers}
\times \text{tokens}
\times \text{KV heads}
\times \text{head dim}
\times 2
\times \text{bytes per value}
$$

The factor of 2 is for keys and values. Grouped-query attention keeps many
query heads but stores fewer key/value heads. That is why a change in model
architecture becomes a serving-system decision: fewer KV heads means more
contexts or users can fit before cache capacity dominates.

## What to implement

Fill in `kv_cache_gib`, then compute:

- `weight_gb`
- `flops_gflop`
- `memory_ms`
- `compute_ms`
- `bottleneck`
- `gqa_cache`
- `mha_cache`

The starter has all constants you need. Do not change the print labels or the
expected values will not line up with the reference output.

## Recap

This exercise is not a simulator. It is a sanity check. If a proposed serving
plan claims a small-batch 70B decode step is faster than the time required to
read the weights, the claim needs a very good explanation: reuse from batching,
lower-bit weights, caching, sparsity, or a different workload phase.
