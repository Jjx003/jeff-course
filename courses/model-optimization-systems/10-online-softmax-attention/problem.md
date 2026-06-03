# Online softmax attention

The previous reading described FlashAttention-style kernels as a memory optimization: stream blocks of keys and values, keep small running statistics, and avoid materializing the full attention matrix. This lab implements the numerical core of that idea for one query row in plain Python.

You will compute attention in two ways:

1. `naive_attention(scores, values)` computes stable softmax over the full score list, then forms the weighted sum.
2. `online_attention(scores, values, block_size)` streams the same scores and values in blocks, updating the running maximum, denominator, and numerator.

Both functions should return the same output vector up to floating-point roundoff. The starter file prints both outputs and their maximum absolute difference.

## The toy setup

The starter file gives one row of attention scores:

$$
x = [1.0,\ 2.0,\ -1.0,\ 0.5]
$$

and four value vectors:

$$
v_1,\dots,v_4 \in \mathbb{R}^2
$$

The attention output is:

$$
o = \sum_i \operatorname{softmax}(x)_i v_i
$$

Real attention scores come from:

$$
x_i = \frac{q \cdot k_i}{\sqrt{d}}
$$

but this lab starts after the dot products. That keeps the focus on softmax, accumulation, and numerical stability.

## What to implement

For the naive path:

- find the maximum score,
- exponentiate every shifted score,
- divide by the denominator,
- compute the weighted sum of value vectors.

For the online path:

- split scores and values into blocks of size `block_size`,
- compute each block's local maximum,
- compute each block's local denominator and unnormalized numerator,
- merge the block into the running state,
- return the final numerator divided by the final denominator.

Keep an unnormalized numerator accumulator. If you store only the normalized output at each step, it is easy to lose the correct rescaling when a later block contains a larger maximum.

## Why the running maximum matters

Softmax is invariant to adding or subtracting the same constant from every score:

$$
\frac{e^{x_i}}{\sum_j e^{x_j}}
=
\frac{e^{x_i-c}}{\sum_j e^{x_j-c}}
$$

Choosing $c=\max_j x_j$ prevents overflow and improves numerical stability. The online recurrence is the blockwise version of the same trick. Every time a new block raises the maximum, the old denominator and numerator must be rescaled into the new coordinate system.

## Lab requirements

Do not change the printed labels. Your program should produce:

- `naive: [...]`
- `online: [...]`
- `max diff: ...`

Round final printed values using the existing code. The expected difference is zero at the printed precision for this toy data.

## Recap

This is the attention-kernel idea without the GPU machinery. A production kernel handles many query rows, heads, masks, and memory layouts. The invariant is the same: keep enough statistics to produce exact softmax attention without writing the full score/probability matrix to memory.
