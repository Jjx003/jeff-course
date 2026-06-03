# Stable streaming

The ordinary softmax formula is:

$$
\operatorname{softmax}(x)_i =
\frac{e^{x_i}}{\sum_j e^{x_j}}
$$

The stable form subtracts the maximum:

$$
\operatorname{softmax}(x)_i =
\frac{e^{x_i-m}}{\sum_j e^{x_j-m}}
$$

where:

$$
m = \max_j x_j
$$

This avoids very large exponentials and preserves the same probabilities.

## Naive attention

For values $v_i \in \mathbb{R}^D$, attention returns:

$$
o = \sum_i p_i v_i
$$

with:

$$
p_i = \frac{e^{x_i-m}}{\sum_j e^{x_j-m}}
$$

One implementation computes all $p_i$ first, then loops over values. That is fine for four scores. It is not fine as the model implementation strategy for long sequences if it requires materializing enormous probability matrices.

## Online attention state

The streaming version keeps three pieces of state:

| Symbol | Meaning |
|---|---|
| $m$ | running maximum score |
| $l$ | running softmax denominator in the coordinate system of $m$ |
| $n$ | running unnormalized weighted value sum |

The normalized output is:

$$
o = \frac{n}{l}
$$

For a new block $b$, compute:

$$
m_b = \max_{j \in b} x_j
$$

$$
l_b = \sum_{j \in b} e^{x_j-m_b}
$$

$$
n_b = \sum_{j \in b} e^{x_j-m_b}v_j
$$

Then merge:

$$
m_\text{new} = \max(m_\text{old}, m_b)
$$

$$
l_\text{new} =
e^{m_\text{old}-m_\text{new}}l_\text{old}
+ e^{m_b-m_\text{new}}l_b
$$

$$
n_\text{new} =
e^{m_\text{old}-m_\text{new}}n_\text{old}
+ e^{m_b-m_\text{new}}n_b
$$

These formulas are exact in real arithmetic. Any difference from naive attention comes from floating-point rounding.

## Worked merge

Imagine the first block has maximum $2.0$ and denominator $l_\text{old}$. A later block has maximum $3.0$. The combined maximum becomes $3.0$, so the old denominator was computed one unit too high in exponent space. Rescale it by:

$$
e^{2.0-3.0} = e^{-1}
$$

The same rescaling applies to the old numerator. This is the step most bugs miss.

## Why production kernels care

In a GPU attention kernel, the "blocks" are tiles chosen to fit shared memory, registers, and tensor-core scheduling. The kernel streams over K/V tiles, updates statistics, and writes the final output. That avoids storing the full $L \times L$ probability matrix.

The lab version uses Python lists, so it will not be fast. That is fine. You are practicing the invariant that makes the fast version possible.

## Numerical caveats

- Initialize the running maximum carefully. Negative infinity is the clean mathematical choice before seeing any block.
- If a block is empty, skip it. The starter data will not create empty blocks, but robust code often checks.
- Use `math.exp`, not an approximation.
- Divide the numerator by the denominator only at the end, or after each merge for inspection. The accumulator itself should remain unnormalized.

## Transition

The next reading returns to serving systems. Once attention can be computed tile by tile, the next major question is where the old keys and values live while thousands of requests decode concurrently.
