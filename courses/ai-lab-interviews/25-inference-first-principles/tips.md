# Rapid-Fire Answers

**"Why is decoding memory-bound?"**
> Each generated token reads every weight from HBM and does about two FLOPs per weight, so arithmetic intensity is roughly the batch size. An H100's ridge point is near 295 FLOP/byte, so at batch 32 you are at maybe 10% of peak compute. Prefill processes many tokens per weight read and sits on the compute-bound side.

**"What is continuous batching?"**
> Scheduling at the iteration level rather than the request level. When a sequence finishes, it is evicted immediately and a queued request takes its slot on the next step, instead of the whole batch waiting for its longest member. Typically a 10–20x throughput improvement over static batching.

**"What does paged attention solve?"**
> Fragmentation, not size. Contiguous per-sequence allocation sized for the maximum length wastes most of its reservation. Fixed-size blocks with a per-sequence block table remove internal fragmentation and give copy-on-write prefix sharing for free.

**"How does speculative decoding keep the output distribution exact?"**
> Accept a draft token with probability `min(1, p_target/p_draft)`; on rejection, sample from the normalized residual `max(0, p_target - p_draft)`. That rejection-sampling scheme provably yields the target distribution. It works because verifying `gamma+1` tokens costs barely more than one in a memory-bound regime.

**"Top-k or top-p?"**
> Top-p, usually. A fixed k is too permissive when the model is confident and too restrictive when it is not; nucleus sampling adapts its cutoff to the shape of each distribution.

**"Throughput is fine but p99 latency is bad. What is happening?"**
> Most likely long prefills blocking decode steps — one 8k-token prompt stalls every sequence already generating. Chunked prefill fixes it by interleaving. Also worth checking: queueing delay from an admission policy that lets the batch grow past the latency budget, and preemption when the KV cache fills.

# Traps

- **Saying "attention is O(n^2) so long context is slow"** without saying which regime. Prefill is quadratic; decode with a cache is linear per token, and the binding constraint there is usually cache *memory*, not compute.
- **Claiming speculative decoding is an approximation.** It is exact. That is its whole selling point.
- **Optimizing throughput when asked about latency.** Name which one you are optimizing, and mention goodput.
- **Forgetting that the KV cache scales with batch.** The per-sequence number is the easy half.
- **Treating weight quantization as a FLOP optimization.** In a bandwidth-bound decode it is a bytes optimization, which is why it works so well.

# Further Reading

- [Efficient Memory Management for LLM Serving with PagedAttention](https://arxiv.org/abs/2309.06180) — the vLLM paper.
- [Orca: A Distributed Serving System for Transformer-Based Generative Models](https://www.usenix.org/conference/osdi22/presentation/yu) — where continuous batching was introduced.
- [Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) — the rejection-sampling proof is short and worth reading.
- [The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751) — nucleus sampling.
- [Efficiently Scaling Transformer Inference](https://arxiv.org/abs/2211.05102)
- The **Model Optimization Systems** track: modules on KV-cache serving, continuous batching, and speculative decoding, with implementations.
