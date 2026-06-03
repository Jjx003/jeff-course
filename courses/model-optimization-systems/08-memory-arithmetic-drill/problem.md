# Memory arithmetic speed drill

Optimization engineers do quick memory estimates constantly. Before a benchmark runs, before a GPU is rented, before a serving limit is promised to a customer, someone usually asks a version of:

- Will the weights fit?
- How much KV cache does this context length consume?
- How many LoRA adapters can sit beside the base model?
- How much work is wasted because this batch is padded?

This drill turns those questions into quick numeric practice. The answers are nearest whole numbers. You are not trying to derive a perfect hardware model; you are building enough taste to catch impossible plans before they waste an afternoon.

## What you will practice

The generated prompts cover five common estimates:

| Quantity | Why it matters |
|---|---|
| BF16 weight memory | Baseline size for unquantized inference and fine-tuning |
| INT4 weight memory | Rough lower bound for weight-only quantized inference |
| LoRA adapter parameters | Cheap task-specific storage compared with a dense matrix |
| KV-cache memory | Main limiter for long-context concurrent serving |
| Padding waste | Hidden throughput loss in naive batching |

Every generated item can be answered from one short formula. Some items use tolerances because real serving calculations often round GB/MB units and metadata differently.

## How to work

Do the arithmetic directly. Keep a scratchpad if you want, but resist reaching for a calculator on every question. The useful skill is the ability to look at a shape and say, "That is about 4 GB," or, "This batch is wasting roughly a third of its token slots."

For example, a 7B-parameter model in BF16 is approximately:

$$
7 \times 2 = 14\ \text{GB}
$$

That estimate ignores small overheads such as metadata, embedding padding, allocator fragmentation, and runtime workspace. It is still the right first number to carry in your head.

## Why the drill comes here

The previous lab showed that a low-rank adapter can be counted with:

$$
r(d_\text{in}+d_\text{out})
$$

The next modules move into attention kernels and serving systems, where the same habit becomes even more valuable. FlashAttention is motivated by avoiding $L^2$ materialization. KV-cache serving is constrained by:

$$
L_\text{layers}H_\text{kv}D_\text{head}2TB_\text{dtype}
$$

Continuous batching improves utilization only if memory and token slots are available. So this drill is a bridge: from one adapter matrix to the arithmetic behind a whole inference server.

## Recap

Approximate memory math is not a replacement for profiling. It is the filter that tells you which profiles are worth running. Aim for fast, explainable answers; the system-specific corrections can come later.
