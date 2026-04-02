# Broadcasting — Solution Walkthrough

## Key Insight

Broadcasting lets you add tensors of different shapes without copying data.
The core rule is simple: **align shapes right-to-left, and every dimension pair must either match or have at least one side equal to 1.**

## Formal Rules

Given shapes $\mathbf{a} = (a_1, a_2, \ldots, a_m)$ and $\mathbf{b} = (b_1, b_2, \ldots, b_n)$, first pad the shorter shape with leading 1s so both have rank $r = \max(m, n)$:

$$a'_i = \begin{cases} 1 & i \le r - m \\ a_{i-(r-m)} & \text{otherwise} \end{cases}$$

Then the output shape $\mathbf{c}$ is computed dimension-by-dimension:

$$c_i = \begin{cases} a'_i & \text{if } a'_i = b'_i \\ b'_i & \text{if } a'_i = 1 \\ a'_i & \text{if } b'_i = 1 \\ \text{ValueError} & \text{if } a'_i > 1 \text{ and } b'_i > 1 \text{ and } a'_i \ne b'_i \end{cases}$$

## Step-by-Step: Computing the Broadcast Shape

For `row` with shape `(1, 3)` and `col` with shape `(2, 1)`:

1. Both already have rank 2, so no padding is needed.
2. Compare dimension by dimension (left to right):
   - Dim 0: $1$ vs $2$ — one side is 1, so output is $2$.
   - Dim 1: $3$ vs $1$ — one side is 1, so output is $3$.
3. Output shape: $(2, 3)$.

For `a` with shape `(3,)` and `b` with shape `(1,)`:

1. Pad to rank 1 (already rank 1).
2. Dim 0: $3$ vs $1$ — output is $3$.
3. Output shape: $(3,)$.

For `x` with shape `(3,)` and `y` with shape `(2,)`:

1. Dim 0: $3$ vs $2$ — both $> 1$ and unequal → `ValueError`.

## `broadcast_shapes` Implementation

```python
def broadcast_shapes(shape_a, shape_b):
    ndim = max(len(shape_a), len(shape_b))
    pa = (1,) * (ndim - len(shape_a)) + tuple(shape_a)
    pb = (1,) * (ndim - len(shape_b)) + tuple(shape_b)

    out = []
    for a, b in zip(pa, pb):
        if a == b:
            out.append(a)
        elif a == 1:
            out.append(b)
        elif b == 1:
            out.append(a)
        else:
            raise ValueError(...)
    return tuple(out)
```

The padding step is the key: `(1,) * (ndim - len(shape_a)) + tuple(shape_a)` prepends the right number of 1s so both padded shapes have the same rank before the per-dimension loop.

## `broadcast_add` Implementation

```python
def broadcast_add(A, B):
    out_shape = broadcast_shapes(A.shape, B.shape)
    ndim = len(out_shape)

    pa = (1,) * (ndim - len(A.shape)) + tuple(A.shape)
    pb = (1,) * (ndim - len(B.shape)) + tuple(B.shape)

    C = Tensor([0.0] * math.prod(out_shape), out_shape)

    for out_idx in itertools.product(*[range(s) for s in out_shape]):
        a_idx = tuple(0 if pa[d] == 1 else out_idx[d] for d in range(ndim))
        b_idx = tuple(0 if pb[d] == 1 else out_idx[d] for d in range(ndim))
        C[out_idx] = A[a_idx] + B[b_idx]

    return C
```

### Index Clamping — The Heart of Broadcasting

For each output index $\mathbf{i} = (i_0, i_1, \ldots, i_{r-1})$, we map back to input indices by **clamping** any broadcast dimension to 0:

$$\text{a\_idx}[d] = \begin{cases} 0 & \text{if } a'_d = 1 \\ i_d & \text{otherwise} \end{cases}$$

This works because a dimension of size 1 means there is only ever one element along that axis — index 0 — and it should be reused for every position in the output.

### Concrete Example

`row` shape `(1, 3)`, `col` shape `(2, 1)`, output shape `(2, 3)`:

| out_idx | a_idx (row) | b_idx (col) | value |
|---------|-------------|-------------|-------|
| (0, 0)  | (0, 0) = 1  | (0, 0) = 10 | 11    |
| (0, 1)  | (0, 1) = 2  | (0, 0) = 10 | 12    |
| (0, 2)  | (0, 2) = 3  | (0, 0) = 10 | 13    |
| (1, 0)  | (0, 0) = 1  | (1, 0) = 20 | 21    |
| (1, 1)  | (0, 1) = 2  | (1, 0) = 20 | 22    |
| (1, 2)  | (0, 2) = 3  | (1, 0) = 20 | 23    |

Dim 0 of `row` is 1, so `a_idx[0]` is always 0.
Dim 1 of `col` is 1, so `b_idx[1]` is always 0.

## Complexity

- Time: $O(N)$ where $N = \prod c_i$ is the number of output elements.
- Space: $O(N)$ for the output buffer.

No data is physically replicated for the inputs — only the output is materialized.
