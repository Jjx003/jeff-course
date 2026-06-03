# KV-cache size

For one request:

$$
\text{bytes} =
L_\text{layers}
\times H_\text{kv}
\times D_\text{head}
\times 2
\times T
\times B_\text{dtype}
$$

This formula appears simple, but every symbol hides a design choice.

| Symbol | Meaning | Serving implication |
|---|---|---|
| $L_\text{layers}$ | transformer layers | deeper models store more cache |
| $H_\text{kv}$ | key/value heads | GQA/MQA reduce cache size |
| $D_\text{head}$ | per-head dimension | tied to attention architecture |
| $2$ | keys and values | both are needed for attention |
| $T$ | cached tokens | prompt plus generated tokens |
| $B_\text{dtype}$ | bytes per value | BF16, FP8, INT8, INT4, etc. |

Example: 32 layers, 8 KV heads, head dimension 128, 8192 cached tokens, BF16:

$$
32 \times 8 \times 128 \times 2 \times 8192 \times 2
\approx 1.07 \times 10^9\ \text{bytes}
$$

That is about 1.1 GB for one request. Ten concurrent requests at that context size can dominate a single GPU even if the weights are quantized.

## MHA, GQA, and MQA

In standard multi-head attention, the number of query heads and KV heads is the same. Grouped-query attention uses fewer KV heads than query heads. Multi-query attention uses one KV head, or one small set, shared across many query heads.

| Attention style | KV-cache pressure | Typical tradeoff |
|---|---|---|
| MHA | highest | maximum per-head flexibility |
| GQA | lower | common modern compromise |
| MQA | lowest | strong cache saving, possible quality tradeoffs |

This is a model architecture decision with serving consequences. Reducing KV heads reduces memory footprint and bandwidth during decode.

## Fragmentation

Two kinds of waste matter:

| Waste type | Example |
|---|---|
| Internal waste | a partly filled fixed-size block |
| External fragmentation | enough total free memory exists, but not in a usable contiguous region |

Paged KV allocation mostly attacks external fragmentation and worst-case reservation. Block size controls the internal waste tradeoff. Smaller blocks waste less at sequence ends but create larger block tables and potentially more overhead. Larger blocks are simpler and more contiguous but can waste more space for short or ending sequences.

## Scheduling pressure

The cache allocator and scheduler are coupled. A scheduler might want to admit a new request, but the cache pool may be full. Possible responses include:

- wait in the queue,
- preempt another request,
- swap cache blocks to CPU memory,
- recompute evicted prefix states later,
- reject the request,
- shorten or chunk prefill,
- lower concurrency limits.

Every choice affects latency and fairness. High throughput is not enough if one long request blocks many short ones or if preemption repeatedly hurts the same user.

## Exact versus approximate systems

It helps to classify serving tricks by whether they preserve the mathematical output:

| Technique | Exact? | Main risk |
|---|---|---|
| Paged KV layout | yes | kernel and allocator complexity |
| Prefix reuse with matching state | yes | unsafe reuse if keys are wrong |
| Continuous batching | yes | latency/fairness tradeoffs |
| KV quantization | approximate unless lossless | retrieval and long-context quality |
| Sliding window attention | changes model context | forgetting distant evidence |
| Token eviction/compression | approximate | task-dependent failures |

The exact/approximate distinction should shape evaluation. Exact layout changes can be tested with numerical equivalence. Approximate cache compression needs downstream task tests.

## Prefix-cache safety

A prefix cache entry is valid only for the same effective computation. Check:

- model weights,
- adapter or merged checkpoint,
- tokenizer and token ids,
- position encoding behavior,
- sampling-independent prefix state,
- tenant/security policy,
- cache salt or isolation key,
- system prompt and tool schema bytes.

A prefix cache bug is dangerous because it can be fast and wrong. In multi-tenant systems, it can also become a data isolation issue.

## Practical measurement

Report at least:

- time to first token,
- output tokens per second,
- request throughput,
- peak KV-cache memory,
- cache hit rate for prefix reuse,
- preemption or swap count,
- p50/p95/p99 latency,
- long-context task quality if compression is enabled.

One average tokens-per-second number is not enough to understand a serving system.
