# Review map

The second half of the course can be organized around four recurring patterns.

## 1. Avoid materializing what you do not need

Attention begins with a large score matrix:

$$
S = \frac{QK^T}{\sqrt{d}}
$$

Naively, the full $S$ matrix and the softmax probabilities can be written to
high-bandwidth memory. FlashAttention-style kernels tile the computation and
maintain enough statistics to compute the exact softmax output without storing
the full attention matrix.

The conceptual tool is online softmax. For a block of scores, keep a running
maximum and denominator so separately processed blocks can be combined exactly.

## 2. Cache the right state

During decode, each new token needs to attend to previous tokens. Recomputing
all previous keys and values would be wasteful, so serving systems store KV
cache entries. The cache grows with:

$$
\text{layers} \times \text{heads} \times \text{context length} \times
\text{head dimension} \times \text{bytes}
$$

This is why long context and high concurrency become memory-management problems.
Paged cache systems treat KV memory more like virtual memory: allocate blocks,
reuse freed space, and avoid large contiguous allocations when requests have
different lengths.

## 3. Keep the batch alive

Static batching waits for a group of requests to move together. Autoregressive
serving is messier: some requests finish early, some receive long prompts, and
new requests arrive while old ones are decoding. Continuous batching admits and
removes work at token granularity so the GPU stays busier.

The tradeoff is scheduler complexity. A good scheduler balances throughput,
fairness, latency, and memory pressure.

## 4. Propose cheaply, verify expensively

Speculative decoding uses a cheap proposal source and target verification. The
rough estimator is:

$$
\text{speedup} \approx
\frac{1 + \sum_{i=1}^{k} a^i}{1 + kc_d}
$$

where $k$ is draft length, $a$ is acceptance probability, and $c_d$ is draft
cost per token. The expression is useful because it says the quiet part out
loud: accepted prefix length is the asset; draft cost is the liability.

Protein modeling has an analogous cascade shape. Cheap PLM embeddings or
variant scores can triage a large candidate set before expensive folding,
co-folding, or affinity prediction. The correctness question changes from
"does the sample match the target distribution?" to "did the cheap screen
preserve the biological candidates we care about?"

## One-page comparison

| Idea | Primary target | Correctness contract |
|---|---|---|
| FlashAttention | Attention memory traffic | Exact attention result |
| KV cache | Decode recomputation | Same logits with reused past state |
| Paged cache | Fragmented serving memory | Correct per-request cache isolation |
| Continuous batching | GPU utilization | Fair scheduling and request isolation |
| Speculative decoding | Decode latency | Target model distribution or target choice |
| Sequence packing | Padding waste | No cross-example leakage |
| Protein cascades | Expensive biological prediction | Preserve relevant candidates |

Use this table as the mental index for the quiz.
