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

## Why batching rescues the MLP but not attention

Module 1 derived that during decode, the weight-reading part of the model has arithmetic intensity $I = 2B/b$: batching helps, because every sequence in the batch reuses the same weights. It is tempting to assume attention inherits that. It does not, and the reason is structural — **each sequence carries its own KV cache**, so there is nothing to share.

Do the accounting for one layer, one decode step, one sequence. Let $H_q$ be query heads, $H_\text{kv}$ key/value heads, $D$ the head dimension, $T$ the cached length, $b$ bytes per stored value.

Bytes read from the cache:

$$
\text{bytes} = 2 \, T \, H_\text{kv} \, D \, b
$$

FLOPs, counting the score computation and the value-weighted sum:

$$
F = \underbrace{2 \, T \, H_q \, D}_{qK^\top} + \underbrace{2 \, T \, H_q \, D}_{pV} = 4 \, T \, H_q \, D
$$

Divide, and watch almost everything cancel:

$$
I_\text{attn} = \frac{4 T H_q D}{2 T H_\text{kv} D b} = \frac{2 H_q}{H_\text{kv}\, b}
$$

The context length $T$ is gone. The head dimension is gone. The batch size never appeared, because doubling the batch doubles both the FLOPs and the bytes. What remains is a constant fixed by two architectural choices:

| Configuration | $H_q/H_\text{kv}$ | cache dtype | $I_\text{attn}$ (FLOP/byte) |
|---|---:|---|---:|
| MHA, BF16 cache | 1 | 2 bytes | 1 |
| GQA-8, BF16 cache | 8 | 2 bytes | 8 |
| GQA-8, FP8 cache | 8 | 1 byte | 16 |
| GQA-8, INT4 cache | 8 | 0.5 bytes | 32 |
| MQA-64, BF16 cache | 64 | 2 bytes | 64 |

Compare every one of those numbers against the H100 ridge point of 295 FLOP/byte from module 1. They are all far below it. **Decode attention is irreducibly memory-bound**, and no scheduling policy, batch size, or kernel can change that — the arithmetic simply is not there. The only two levers are the two in the formula: raise the query-to-KV head ratio, or shrink the bytes per entry.

That is the honest justification for grouped-query attention, and it is a far better one than "GQA saves memory." GQA saves *bandwidth on the critical path of every generated token*, and the formula says exactly how much: the speedup is linear in $H_q/H_\text{kv}$ for as long as attention dominates the step.

It also explains a puzzle you will hit in benchmarks. If you raise the batch size, the MLP's intensity climbs toward the ridge point while attention's stays pinned at 8. Past some batch size, attention stops being a modest fraction of the decode step and becomes the majority of it, because it is the one part that refused to get faster. Serving stacks hit this wall at long context, which is where the cache-compression literature comes from.

## MHA, GQA, and MQA

In standard multi-head attention, the number of query heads and KV heads is the same. Grouped-query attention uses fewer KV heads than query heads. Multi-query attention uses one KV head, or one small set, shared across many query heads.

![Diagram comparing multi-head attention with H key and value heads, grouped-query attention with one key and value head per group of queries, and multi-query attention with a single shared key and value head](/courses/model-optimization-systems/kv-gqa-fig2-mha-gqa-mqa.png)

*Figure 2 from Ainslie et al., GQA (CC BY 4.0). The query row is unchanged in all three; only the number of distinct K and V heads varies.*

| Attention style | KV-cache pressure | Typical tradeoff |
|---|---|---|
| MHA | highest | maximum per-head flexibility |
| GQA | lower | common modern compromise |
| MQA | lowest | strong cache saving, possible quality tradeoffs |

This is a model architecture decision with serving consequences. Reducing KV heads reduces memory footprint and bandwidth during decode.

Two further points make GQA a practical option rather than a design you must commit to before pretraining.

**You can convert an existing checkpoint.** Uptraining takes a trained MHA model, mean-pools the key and value heads within each group to initialize the reduced heads, and continues pretraining for a small fraction $\alpha$ of the original steps — around 5 percent. Mean-pooling rather than selecting one head matters: it preserves the average behavior of the group, so the model starts near a working configuration instead of having discarded seven eighths of its cache projections.

**The number of groups is not a free parameter in a sharded deployment.** Under standard tensor parallelism across $P$ devices, a single MQA key/value head has to be replicated on every device, so you pay for it $P$ times and recover less than the head count suggests. Choosing $G = P$ means each shard owns exactly one KV head with no replication at all. This is why GQA-8 is so common: eight groups is not a quality sweet spot discovered by ablation so much as the shape that matches an eight-way tensor-parallel node.

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

## Not every cached token is equally droppable

The obvious way to bound cache growth is a sliding window: keep the most recent $W$ tokens, evict the rest. It is simple, it caps memory exactly, and on a plain implementation it destroys the model. Perplexity does not degrade gracefully as the window slides past the start of the text — it explodes, the moment the *first few tokens* are evicted.

The explanation is a property of softmax rather than of language. Attention weights are forced to sum to one. When a head has nothing it genuinely needs to attend to at a given position — which is most heads, most of the time — it still has to put its probability mass somewhere. Under causal masking, the only positions visible to every query are the first ones, so training reliably recruits them as a dumping ground. They are **attention sinks**, and their content is close to irrelevant; their *position* is the point.

![Heatmaps of average attention logits for several layers and heads of Llama-2-7B, showing a local recency pattern in the first two layers and a strong vertical stripe on the initial token in all deeper layers](/courses/model-optimization-systems/kv-streamingllm-fig2-attention-sinks.png)

*Figure 2 from Xiao et al., StreamingLLM (CC BY 4.0). Layers 0 and 1 show the local, recency-weighted pattern one would expect. Every deeper layer shows a saturated vertical stripe on token 0 — attention going to the first token regardless of what that token says.*

The fix is correspondingly cheap: keep four sink tokens permanently, then a rolling window of recent tokens. That combination holds perplexity stable out to four million tokens on models trained with a 4K window. A second detail is easy to get wrong — positions must be assigned by index *within the cache*, not by the token's original offset in the text, or the model is asked to extrapolate to position encodings it never saw.

The transferable lesson is larger than this one technique. A cache-eviction policy that looks semantically reasonable — "old tokens matter less" — can be catastrophic, because some entries are load-bearing for reasons that have nothing to do with their meaning. Any compression scheme in the next section needs to be evaluated against that possibility rather than against intuition.

## Prefill and decode want different machines

One last scheduling tension follows directly from the roofline. Prefill is compute-bound: a long prompt reuses each weight many times and pushes past the ridge point. Decode is memory-bound and sits far below it. Putting both in the same batch on the same device means each is running on hardware tuned for the other, and worse, a single long prefill monopolizes the step and stalls every decode sharing it — visible to users as an inter-token latency spike that correlates with *somebody else's* long prompt.

Two standard responses:

- **Chunked prefill.** Split a long prefill into fixed-size token chunks and co-schedule each chunk with ongoing decodes. Total prefill work is unchanged, but the worst-case stall a decode can suffer is now bounded by the chunk size instead of by the longest prompt in the queue.
- **Prefill/decode disaggregation.** Run the two phases on separate GPU pools and ship the KV cache between them. Each pool can then be sized, batched, and even parallelized differently, since one is optimizing time-to-first-token under a compute bound and the other output tokens per second under a bandwidth bound. The cost is moving the cache across the interconnect, which is why this trade only pays above a certain scale.

Both are the same observation as the whole course: when one resource is scarce for one phase and abundant for another, stop treating the two phases as the same workload.

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

## Going deeper

- PagedAttention and vLLM: https://arxiv.org/abs/2309.06180
- GQA, uptraining multi-head checkpoints into grouped-query models: https://arxiv.org/abs/2305.13245
- Multi-query attention, the original single-KV-head proposal: https://arxiv.org/abs/1911.02150
- StreamingLLM and attention sinks: https://arxiv.org/abs/2309.17453
- vAttention, keeping the cache virtually contiguous instead of paging it: https://arxiv.org/abs/2405.04437
- Sarathi-Serve, chunked prefill and stall-free batching: https://arxiv.org/abs/2403.02310
- DistServe, disaggregating prefill from decode: https://arxiv.org/abs/2401.09670
- H2O, heavy-hitter oracle for KV cache eviction: https://arxiv.org/abs/2306.14048
- vLLM documentation on automatic prefix caching: https://docs.vllm.ai/en/latest/design/automatic_prefix_caching.html
