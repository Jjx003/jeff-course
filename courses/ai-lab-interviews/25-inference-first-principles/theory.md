# The KV Cache

## What it is

During decoding, attention at step $t$ needs the keys and values for all positions $1..t$. Those depend only on tokens already generated, so recomputing them each step would be pure waste. Cache them instead.

**Without a cache:** generating $n$ tokens costs $O(n^3)$ total attention work, because each step reprocesses the whole prefix.
**With a cache:** $O(n^2)$, and each individual step is $O(t)$.

## What it costs

$$\text{bytes} = 2 \cdot L \cdot G \cdot d_h \cdot b \cdot S \cdot \text{dtype bytes}$$

The 2 is K and V. Llama-2-70B (80 layers, 8 KV heads, $d_h$ 128, bf16) works out to about 0.33 MB per token:

| Context | Per sequence | Batch 32 |
|---|---|---|
| 4k | 1.3 GB | 43 GB |
| 32k | 11 GB | 344 GB |
| 128k | 43 GB | 1.4 TB |

The weights are 140 GB. At 32k context and batch 32 the cache is more than twice the model. **That is the whole story of modern LLM serving.**

![Two panels showing KV cache size against context length and against batch size for MHA, GQA and MQA, against an HBM headroom line.](/courses/ai-lab-interviews/kv-cache-growth.svg)

## What to do about it

- **GQA** — fewer KV heads. 4–8x, essentially free in quality. Already covered.
- **KV quantization** — int8 or int4 keys and values. 2–4x, and unlike weights it must be done at runtime, per token, which constrains how clever the scheme can be. Keys are typically more outlier-prone than values.
- **Paged attention** — see below.
- **Eviction / sliding window** — drop old tokens. Cheap and lossy, and it interacts badly with attention sinks: naively evicting the earliest tokens destroys quality, so streaming schemes pin the first few permanently.
- **Prefix sharing** — many requests share a long system prompt. Cache it once and reference it from every sequence. Enormous in practice, and often the first thing to try. Production servers now do this automatically (vLLM's prefix caching, SGLang's RadixAttention, which keeps a radix tree of all cached prefixes), and the multi-turn-agent traffic pattern — same growing prefix re-sent every turn — is exactly what it is built for.
- **Architectural compression** — DeepSeek's MLA (multi-head latent attention) is the strongest published version: cache one small latent vector per token instead of per-head K and V, and decompress on the fly. It cut DeepSeek-V2/V3's cache by an order of magnitude relative to MHA and is the reason those models serve long contexts cheaply.

# Batching

## Why static batching fails

Group requests, run them together, return when all finish. The problem is that generation lengths vary by an order of magnitude: a batch of 32 where one request wants 2000 tokens and the rest want 50 keeps 31 slots idle for the entire tail.

## Continuous batching

Schedule at the **iteration** level rather than the request level. When a sequence emits its EOS, evict it immediately and admit a waiting request into that slot on the very next step.

Reported throughput improvements are large — often 10–20x over naive static batching — because GPU utilization stops being hostage to the longest request in each batch. This is the single most important idea in LLM serving and the answer to a very common question.

## Chunked prefill

A long prefill blocks every decode step behind it, spiking inter-token latency for everyone already generating. Chunked prefill splits a long prompt into pieces and interleaves them with decode steps, trading a little TTFT for a lot of TPOT stability. Modern servers do this by default.

## Disaggregated prefill and decode

The 2025-era refinement: stop making one GPU pool do both jobs. Prefill is compute-bound and decode is bandwidth-bound, so co-locating them means each interferes with the other's latency target. Disaggregated serving runs prefill on one pool of GPUs and decode on another, shipping the finished KV cache across the interconnect between them. The costs are the KV transfer itself (RDMA, overlapped with computation) and operating two pools whose relative sizes must track the workload's prompt-to-generation ratio. Kimi's Mooncake was the first prominent public writeup; the idea is now standard in vLLM, SGLang, and production stacks at the big labs, and "when would you disaggregate?" is a live interview question — the answer is: at scale, when tight TTFT *and* TPOT targets must hold simultaneously under mixed traffic.

![Two timelines. The top shows a single colocated GPU where a 120 ms prefill blocks a regular cadence of 12 ms decode steps, leaving a 132 ms gap with no tokens. The bottom shows a separate prefill pool and decode pool, where the decode cadence is uninterrupted.](/courses/ai-lab-interviews/prefill-decode-disaggregation.svg)

## Paged attention

The problem it solves is **memory fragmentation**, not memory size.

Naively, you allocate each sequence a contiguous cache buffer sized for its maximum possible length. A request that stops after 100 tokens with a 4096-token reservation wastes 97% of its allocation, and the free space is scattered in unusable fragments.

Paged attention borrows virtual memory: the cache is stored in fixed-size blocks (typically 16 tokens), with a per-sequence block table mapping logical positions to physical blocks. Blocks are allocated on demand and freed on completion.

Consequences worth naming:

- Near-zero internal fragmentation, so effective batch size rises a lot.
- **Copy-on-write sharing** falls out for free: parallel samples from one prompt, or many requests sharing a system prompt, can point at the same physical blocks until they diverge.

# Sampling

![Three panels showing one next-token distribution under temperature, top-k, and top-p, on a log scale.](/courses/ai-lab-interviews/sampling-strategies.svg)

**Greedy** — take the argmax. Deterministic, and degenerate on open-ended text: it loops.

**Temperature** — divide logits by $T$ before the softmax. $T<1$ sharpens, $T>1$ flattens, $T\to0$ approaches greedy. Note it rescales the *whole* distribution rather than truncating it.

**Top-k** — keep the $k$ highest-probability tokens, renormalize. Simple; the flaw is that a fixed $k$ is too permissive when the model is confident (admitting nonsense into a near-deterministic step) and too restrictive when it is uncertain.

**Top-p (nucleus)** — keep the smallest set whose cumulative probability reaches $p$, renormalize. The cutoff adapts to the shape of each distribution, which is exactly the fix for top-k's flaw. This is why top-p is the more common default.

**Min-p** — keep tokens with probability at least $p \times p_{\max}$. A threshold relative to the top token; more robust at high temperature.

**Repetition and frequency penalties** — subtract from the logits of tokens already generated. Blunt instruments, and they can damage legitimate repetition such as code indentation or a repeated name.

The order matters: penalties, then temperature, then truncation, then renormalize. Getting it wrong changes behavior in ways that are hard to debug.

# Speculative Decoding

A small draft model proposes $\gamma$ tokens; the large target model verifies all of them **in a single forward pass**, because verification is a parallel prefill-like operation over $\gamma+1$ positions.

The rejection-sampling scheme accepts draft token $x$ with probability $\min(1, p_{target}(x)/p_{draft}(x))$ and, on rejection, samples from the normalized residual $\max(0, p_{target} - p_{draft})$.

**The property that makes it interesting:** the output distribution is *exactly* the target model's. It is not an approximation. That is the thing to say, and it is what distinguishes speculative decoding from every other inference speedup, which all trade quality for speed.

**Why it works at all:** decode is memory-bound, so verifying $\gamma+1$ tokens costs barely more than verifying one — you read the weights once either way. You are spending idle compute to buy back memory-bandwidth-limited steps.

**The expected yield** with per-token acceptance rate $\alpha$:

$$\mathbb{E}[\text{tokens per verification}] = \frac{1-\alpha^{\gamma+1}}{1-\alpha}$$

One rejection ends the run, so the tail is geometric and returns diminish quickly in $\gamma$. Dividing by the draft's own cost gives the wall-clock optimum, which lands at a surprisingly short draft length.

![Two panels: expected accepted tokens against draft length for four acceptance rates, and wall-clock speedup against draft length for four draft costs, each with a marked optimum.](/courses/ai-lab-interviews/speculative-decoding.svg)

**Variants worth naming:** Medusa (extra prediction heads on the target model instead of a separate draft model), EAGLE (drafting in feature space), and n-gram or prompt-lookup drafting (no model at all — copy candidate continuations from the prompt, which works startlingly well for summarization and code editing).

# Quantization for Serving

**Weight-only (int8, int4)** is the highest-leverage move, precisely because decode is bandwidth-bound: halving the bytes read per token nearly halves the time per token. The weights are dequantized on the fly and the matmul still runs in bf16, so it buys bandwidth rather than FLOPs — which is exactly what a memory-bound workload needs.

**Activation quantization** additionally buys FLOPs but is harder, because activations have outliers that weights do not. SmoothQuant migrates the difficulty from activations into weights by rescaling; AWQ protects the salient weight channels identified by activation statistics.

**KV-cache quantization** attacks the other half of the memory. It must happen at runtime, so the scheme has to be cheap.

The **Model Optimization Systems** track in this library covers all of this properly, with implementations.
