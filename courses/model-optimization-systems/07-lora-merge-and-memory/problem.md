# Merge LoRA and count the memory

LoRA is one of the most useful tricks in modern model optimization because it separates two questions that are often tangled together:

1. How large is the base model?
2. How much new information do I need to store for this task?

The answer to the second question can be surprisingly small. Instead of fine-tuning every entry of a dense weight matrix $W$, LoRA freezes $W$ and learns a low-rank correction:

$$
W' = W + \frac{\alpha}{r}BA
$$

In this lab you will implement that operation for a tiny matrix using plain Python lists. The numbers are deliberately small enough to inspect by hand. The point is not to build a fast linear algebra library; the point is to make the memory arithmetic and matrix shapes feel obvious.

You are given:

- a base matrix $W$,
- a down/up LoRA factor pair $A$ and $B$,
- a scaling constant `ALPHA`.

Your program should print:

1. the LoRA scale,
2. the dense matrix parameter count,
3. the adapter parameter count,
4. the adapter percentage,
5. the delta matrix,
6. the merged matrix.

Use the exact data already in the starter file. Keep the printed formatting unchanged so the deterministic grader can compare your output.

## Why this tiny example matters

In a transformer, most trainable parameters live in matrix multiplications: attention projections, MLP projections, and sometimes embedding/output projections. A dense fine-tune of a $4096 \times 4096$ matrix would update about 16.8 million values for that one matrix alone. A rank-16 LoRA adapter for the same square matrix stores:

$$
16(4096 + 4096) = 131072
$$

trainable values, less than 1 percent of the dense matrix. That adapter can be saved, loaded, swapped, composed with other adapters in limited cases, or merged into the base model for deployment.

Your toy example has the opposite ratio: the adapter has more parameters than the base matrix. That is intentional. At small dimensions the fixed overhead of two factor matrices overwhelms the saving. LoRA becomes compelling when $d_\text{in}$ and $d_\text{out}$ are thousands and the rank $r$ stays small.

## Merge versus keep separate

During training, the usual computation is:

$$
y = Wx + \frac{\alpha}{r}B(Ax)
$$

This is convenient because only $A$ and $B$ receive gradient updates. During inference, you have a choice:

| Strategy | What happens | When it is useful |
|---|---|---|
| Keep adapter separate | Compute base path plus adapter path | Many adapters share one base model |
| Merge adapter | Precompute $W' = W + \frac{\alpha}{r}BA$ | One adapter is served heavily and latency matters |
| Quantized base plus adapter | Store base in low precision, adapter often higher precision | QLoRA-style fine-tuning and memory-constrained serving |

Merging removes the extra adapter matmuls at inference time, but it also turns a cheap adapter artifact into a full modified matrix. Production systems often keep adapters separate when they need to hot-swap hundreds of customer-specific adapters on the same base model. They merge when the adapter is stable, popular, and worth baking into a deployment artifact.

## Lab requirements

Implement three helpers:

- `matmul(left, right)` for nested-list matrix multiplication,
- `add(left, right)` for elementwise matrix addition,
- `scale_matrix(matrix, scale)` for scalar multiplication.

Then compute:

$$
\Delta W = \frac{\alpha}{r}BA
$$

and:

$$
W' = W + \Delta W
$$

The starter file already computes `rank`, `scale`, `dense_params`, and `adapter_params`. You only need to fill in the missing operations.

## Recap

LoRA is a low-rank delta on top of a frozen dense matrix. The same formula supports two very different deployment modes: keep the adapter separate for flexibility, or merge it for simpler inference. The next drill turns this kind of arithmetic into fast estimation practice: weights, adapters, KV caches, and padding waste.
