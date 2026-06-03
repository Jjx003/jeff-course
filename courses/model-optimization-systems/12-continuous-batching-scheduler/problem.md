# Continuous batching scheduler

Traditional batching waits for a whole batch to finish. Continuous batching admits new requests as soon as capacity opens.

That sounds like a small scheduling tweak, but it is one of the main reasons modern LLM servers can keep GPUs busy under real traffic. Decode requests do not all have the same output length. Some finish after one token. Some stream for hundreds. If a server locks a static batch until the slowest sequence finishes, completed requests leave holes that no new work can use.

In this lab you will simulate a tiny decode scheduler:

- each request has an arrival time and a number of output tokens,
- at each tick, admit waiting requests until `MAX_ACTIVE` is reached,
- every active request generates one token per tick,
- completed requests leave before the next tick,
- print the timeline and completion times.

This is a simplified model of the scheduling idea behind high-throughput LLM serving. It omits prefill, KV-cache blocks, tokenization, streaming I/O, priorities, and GPU kernels, but the core loop is recognizable: maintain a running batch, remove finished sequences, and admit new ones.

## The provided workload

The starter file defines:

```python
REQUESTS = [
    {"id": "A", "arrival": 0, "tokens": 3},
    {"id": "B", "arrival": 0, "tokens": 1},
    {"id": "C", "arrival": 1, "tokens": 2},
    {"id": "D", "arrival": 2, "tokens": 2},
]

MAX_ACTIVE = 2
```

At tick 0, requests A and B can start. Both generate one token. B is done immediately, so at tick 1 a slot is available for C. This is the key continuous-batching behavior: C does not wait for A to finish.

## What to implement

Write `simulate(requests, max_active)` so it returns:

1. `timeline`: a list of `(tick, active_ids_before_generation)` pairs,
2. `completed`: a dictionary mapping request id to finish tick.

The starter code prints:

```text
t=0: active=A,B
...
completed: A:3 B:1 C:3 D:5
```

Do not change the printed format. The deterministic grader checks the timeline and completion line.

## Timing convention

Use this convention:

- A request with `arrival <= tick` may be admitted at the start of that tick.
- The timeline records active request ids before token generation for that tick.
- Every active request generates one token during the tick.
- A request that reaches zero remaining tokens completes at the end of the tick.
- Its finish time is `tick + 1`.
- Completed requests are removed before the next tick.

This is why request B, which needs one token at tick 0, finishes at time 1.

## Why this matters in real serving

Real engines such as vLLM and TensorRT-LLM use iteration-level or in-flight batching ideas: the active set can change between decode iterations. The scheduler is constrained by more than `MAX_ACTIVE`, though. It must consider:

- available KV-cache blocks,
- maximum batched tokens,
- prompt prefill work,
- decode fairness,
- streaming response deadlines,
- cancellations,
- priority classes,
- speculative decoding,
- prefix cache hits,
- adapter routing.

Your simulator uses a request-count capacity because it is easy to inspect. Production systems usually care about token capacity and memory capacity.

## Recap

Continuous batching converts idle slots into useful decode work. The concept is simple; the production version is a careful negotiation between GPU utilization, KV-cache memory, and user-visible latency.
