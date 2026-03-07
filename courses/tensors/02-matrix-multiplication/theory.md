# Theory: Matrix Multiplication

## Definition

Given $A \in \mathbb{R}^{m \times k}$ and $B \in \mathbb{R}^{k \times n}$, the product
$C = AB \in \mathbb{R}^{m \times n}$ is defined element-wise as:

$$C_{ij} = \sum_{l=0}^{k-1} A_{il} \cdot B_{lj}$$

Each output element $C_{ij}$ is an **inner product** between row $i$ of $A$ and column $j$ of $B$.

---

## The Naive Algorithm

```
for i in range(m):
    for j in range(n):
        acc = 0
        for l in range(k):
            acc += A[i, l] * B[l, j]
        C[i, j] = acc
```

Complexity: $O(mnk)$. For square matrices: $O(n^3)$.

---

## Cache Behaviour

Modern CPUs are fast; **memory latency** is the bottleneck. The naive ijk loop
accesses `B` column-by-column, which is **cache-unfriendly** for row-major storage:

```
B accessed as: B[0,j], B[1,j], B[2,j] ...
               ↑ these are stride-n apart in memory → cache misses
```

### ikj Loop Order (cache-friendly)

Reordering to **ikj** keeps the inner loop accessing consecutive elements of `B`:

```
for i in range(m):
    for l in range(k):       # ← moved k-loop outward
        for j in range(n):   # ← B[l, j] is now contiguous!
            C[i,j] += A[i,l] * B[l,j]
```

The inner loop now streams through a full row of `B`, maximising cache line usage.

---

## Block / Tiled MatMul

For large matrices, even ikj misses because `C` and `A` rows don't fit in L1 cache.
**Tiling** splits matrices into small blocks that each fit in cache:

$$C_{IJ} = \sum_{L} A_{IL} \cdot B_{LJ}$$

where $I, J, L$ are block indices. This is the foundation of BLAS `dgemm`.

---

## Why This Matters

Every layer in a neural network is ultimately a matrix multiplication:

- Linear layer: $Y = XW^T$
- Attention: $\text{softmax}(QK^T/\sqrt{d_k}) \cdot V$

GPUs achieve TeraFLOP/s of matmul throughput using thousands of cores and
hardware-accelerated tensor cores.
