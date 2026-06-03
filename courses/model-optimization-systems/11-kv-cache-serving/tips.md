# Practical hints

Track maximum concurrency in tokens, not just requests. A batch of four 32k-context requests can be more expensive than dozens of short chats.

## Debugging questions

- How many KV heads does the model actually use?
- Are cache tensors BF16, FP8, INT8, or another format?
- Is prefix caching enabled, and what is the hit rate?
- Are requests preempted, swapped, or recomputed under load?
- Does the benchmark include cancellations and varied output lengths?
- Is long-context quality measured after compression?

## Memory planning

Start from the formula:

$$
L_\text{layers}H_\text{kv}D_\text{head}2TB_\text{dtype}
$$

Then add:

- weights,
- activations/workspace,
- allocator slack,
- adapter memory,
- runtime metadata,
- safety headroom for traffic spikes.

If the sum only fits on paper with no slack, it probably will not fit calmly in production.

## Evaluation traps

- Prefix caching can make a benchmark look excellent if every prompt shares a template, then disappoint on diverse traffic.
- KV compression can pass chat-style tests but fail retrieval tasks.
- Paged allocation improves utilization, but kernel support and block size still matter.
- A low average latency can hide poor tail latency when long requests occupy cache.

## Going deeper

- vLLM / PagedAttention: https://arxiv.org/abs/2309.06180
- vAttention: https://arxiv.org/abs/2405.04437
- TensorRT-LLM KV cache documentation: https://nvidia.github.io/TensorRT-LLM/features/kvcache.html
- TensorRT-LLM KV cache reuse: https://nvidia.github.io/TensorRT-LLM/advanced/kv-cache-reuse.html
