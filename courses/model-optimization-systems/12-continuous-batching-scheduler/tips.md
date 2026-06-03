# Hints

Keep the simulation small and explicit. You do not need threads, async code, or real time.

## Suggested representation

Convert each request into a mutable record with:

- `id`,
- `arrival`,
- `remaining`.

Keep:

- `active` as a list of currently running records,
- `completed` as a dictionary,
- `tick` as an integer.

## Loop structure

At each tick:

1. Admit requests whose `arrival <= tick` while there is capacity.
2. Record `active_ids_before_generation`.
3. Decrement `remaining` for every active request.
4. Move newly completed requests into `completed` with finish time `tick + 1`.
5. Remove completed requests from `active`.
6. Advance `tick`.

Continue until every request is completed.

## Ordering

Use the order in `REQUESTS` as the queue order. That makes the output deterministic. When two requests arrive at the same time, the earlier one in the list should be admitted first.

For the provided data:

- A and B enter at tick 0.
- B completes at time 1.
- C enters at tick 1.
- A and C complete at time 3.
- D enters at tick 3, because capacity is checked at the start of each tick.

## Common bugs

- Recording the timeline after decrementing tokens instead of before generation.
- Marking completion as `tick` instead of `tick + 1`.
- Admitting request D at tick 2 even though A and C are still active at the start of tick 2.
- Forgetting to continue ticking after the last request has arrived but active work remains.
- Mutating the global `REQUESTS` in a way that would break repeated calls.

## Going deeper

- vLLM project: https://www.vllm.ai/
- TensorRT-LLM in-flight batching documentation: https://nvidia.github.io/TensorRT-LLM/features/paged-attention-ifb-scheduler.html
- vLLM PagedAttention paper: https://arxiv.org/abs/2309.06180
