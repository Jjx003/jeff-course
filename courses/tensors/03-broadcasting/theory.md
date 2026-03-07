# Theory: Broadcasting

## Motivation

Without broadcasting, adding a bias vector to every row of a matrix would
require explicit loops or memory duplication. Broadcasting makes this implicit
and zero-copy.

```python
# Without broadcasting (manual loop):
for i in range(m):
    for j in range(n):
        C[i, j] = A[i, j] + b[j]

# With broadcasting (conceptual):
C = A + b   # b has shape (n,) → treated as (1, n) → broadcast to (m, n)
```

---

## The Rules

Align shapes from the **right**:

```
A:     (4, 1, 6)
B:        (5, 6)
─────────────────
out:   (4, 5, 6)
```

Step by step:
- Dim -1: `6 == 6` → `6`
- Dim -2: `1` vs `5` → `5` (A is stretched)
- Dim -3: `4` vs missing (treated as `1`) → `4` (B is stretched)

---

## Implementation Strategy

### Option A: Index arithmetic (zero-copy simulation)

For each output index $(i_0, \ldots, i_{k-1})$, compute the corresponding
index into `A` and `B` by **clamping** each index to `min(idx, size-1)`:

$$a_{\text{idx}} = \min(i_j,\; \text{shape}_A[j] - 1)$$

This simulates "repeating" the size-1 dimension without allocating extra memory.

### Option B: Stride tricks

Set stride to `0` for any broadcast dimension. Then the flat offset computation
naturally repeats the same element:

$$\text{offset} = \sum_j i_j \cdot s_j \quad \text{where } s_j = 0 \text{ if dim}_j = 1$$

This is exactly how NumPy implements broadcasting internally.

---

## Why Broadcasting Matters for Deep Learning

Broadcasting is pervasive in neural networks:

| Operation          | Broadcasting pattern |
|--------------------|----------------------|
| Add bias           | `(batch, n) + (n,)` |
| Layer norm scale   | `(batch, seq, d) * (d,)` |
| Attention mask     | `(batch, heads, seq, seq) + (1, 1, seq, seq)` |

Understanding broadcasting is essential for reading and debugging tensor code.
