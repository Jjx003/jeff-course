# Inference From First Principles

Almost every inference question has the same answer underneath it, and it is this:

> **Decoding is memory-bandwidth bound. Each generated token requires reading every weight from HBM and performing only about two FLOPs per weight, so arithmetic intensity is roughly the batch size — far below what the hardware needs to saturate its compute.**

Continuous batching, GQA, weight-only quantization, KV-cache quantization, speculative decoding, paged attention: every one of them is a response to that sentence. If you can derive the sentence, you can reason your way to all of them live rather than reciting a list.

![A roofline plot for an H100 with prefill and several decode batch sizes placed on it by arithmetic intensity, showing batch-1 decode at well under 1% of peak.](/courses/ai-lab-interviews/roofline-decode.svg)

## Two phases, two regimes

| | Prefill | Decode |
|---|---|---|
| Processes | the whole prompt at once | one token per sequence |
| Parallelism | across all prompt tokens | across the batch only |
| Arithmetic intensity | high | ≈ batch size |
| Bound by | compute | memory bandwidth |
| Latency metric | time to first token (TTFT) | time per output token (TPOT) |
| Scales with | prompt length (quadratically in attention) | context length (cache reads) |

They are different enough that serious serving systems schedule them separately — and "prefill/decode disaggregation" is a good thing to know the name of.

## What gets asked

- Why is decoding memory-bound and prefill compute-bound?
- Walk me through what a KV cache stores and what it costs.
- What is continuous batching and what does it fix?
- Implement top-k / top-p sampling. When would you use each?
- How does speculative decoding preserve the output distribution?
- What is paged attention and what problem does it solve?
- Your p99 latency is bad but throughput is fine. What is happening?

## The metrics vocabulary

Getting these right matters, because they trade against each other and an interviewer will ask you which one you are optimizing.

- **TTFT** — time to first token. Dominated by prefill, so by prompt length.
- **TPOT** / **ITL** — time per output token, or inter-token latency. Dominated by decode, so by memory bandwidth and batch size.
- **Throughput** — total tokens per second across all requests. Improved by larger batches.
- **Goodput** — throughput that actually meets your latency SLO. The one that matters, and the one people forget to name.

The central tension: **larger batches raise throughput and worsen per-request latency.** Any serving question is somewhere on that curve.
