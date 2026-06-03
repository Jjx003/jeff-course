# Practical hints

## How to evaluate a speculative system

Do not start by asking, "What is the advertised speedup?" Start with a table:

| Measurement | Why you need it |
|---|---|
| Acceptance rate by workload | Average acceptance can hide bad domains. |
| Draft latency per token | A slow draft can erase the gain. |
| Target verification latency | The verification pass may not equal one ordinary decode step. |
| Extra memory | Draft weights, draft KV cache, and target cache all matter. |
| Time to first token | Some designs help decode but add setup latency. |
| p50/p95/p99 latency | Users feel tail latency, not just mean speed. |
| Tokens/sec at saturation | Latency wins can disappear when the GPU is fully throughput-bound. |

For a local experiment, log every speculative step:

```text
request_id, draft_len, accepted, rejected_at, target_ms, draft_ms, committed
```

That one row lets you compute acceptance, committed tokens per verification, and
whether a particular request pattern is helping.

## Common failure modes

- The draft model is small but hosted inefficiently.
- The draft and target use different tokenizers or chat templates.
- High-temperature sampling lowers acceptance enough to remove the benefit.
- Grammar-constrained decoding rejects draft tokens frequently.
- Extra cache memory reduces batch size.
- Benchmark prompts are repetitive, while production prompts are diverse.
- The implementation reports tokens/sec but ignores time to first token.

## How this connects to the next lab

In the simulator, keep the mental picture simple:

1. Drafting buys a possible multi-token advance.
2. Rejections shorten the accepted prefix.
3. Draft cost must be subtracted from the gain.

You are not modeling every kernel. You are learning to recognize when a claimed
speedup is plausible.

## Going deeper

- Compare greedy decoding, temperature sampling, and constrained JSON decoding
  separately.
- Try an acceptance histogram instead of a single average.
- Treat protein screens the same way: cheap embedding, expensive structure
  model, retained fraction, false-negative risk.
