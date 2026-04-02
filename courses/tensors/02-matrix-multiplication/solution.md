# Solution: Matrix Multiplication

## Key Insight

Matrix multiplication is defined element-wise by a dot product between each
row of $A$ and each column of $B$. For matrices $A \in \mathbb{R}^{m \times k}$
and $B \in \mathbb{R}^{k \times n}$, the output $C \in \mathbb{R}^{m \times n}$
satisfies:

$$C_{ij} = \sum_{p=0}^{k-1} A_{ip} \cdot B_{pj}$$

Every element of $C$ requires a full dot product over the shared inner
dimension $k$. This gives us three independent loops — over $i$, $j$, and $p$
— which is the origin of the "triple loop" algorithm.

## Algorithm

### Step 1 — Validate shapes

Before doing any arithmetic, verify that $A$'s column count equals $B$'s row
count. If $A$ is $(m, k)$ and $B$ is $(k', n)$, we need $k = k'$; otherwise the
summation index $p$ is undefined.

```python
m, k = A.shape
k2, n = B.shape
if k != k2:
    raise ValueError(f"Inner dimensions must match: ...")
```

### Step 2 — Allocate the output

Allocate $C$ as an $(m \times n)$ tensor filled with zeros. Using integer zeros
ensures that integer inputs produce integer outputs without floating-point noise.

```python
C = Tensor([0] * (m * n), (m, n))
```

### Step 3 — Triple loop

```python
for i in range(m):       # row of A / row of C
    for j in range(n):   # col of B / col of C
        acc = 0
        for p in range(k):           # shared inner dimension
            acc += A[i, p] * B[p, j]
        C[i, j] = acc
```

The innermost variable `acc` accumulates the dot product, and is written to
$C$ only once per $(i, j)$ pair — this avoids redundant index computations
inside the $p$ loop.

## Worked Example

With

$$A = \begin{pmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \end{pmatrix}, \quad
B = \begin{pmatrix} 7 & 8 \\ 9 & 10 \\ 11 & 12 \end{pmatrix}$$

the four output elements are:

$$C_{00} = 1 \cdot 7 + 2 \cdot 9 + 3 \cdot 11 = 7 + 18 + 33 = 58$$

$$C_{01} = 1 \cdot 8 + 2 \cdot 10 + 3 \cdot 12 = 8 + 20 + 36 = 64$$

$$C_{10} = 4 \cdot 7 + 5 \cdot 9 + 6 \cdot 11 = 28 + 45 + 66 = 139$$

$$C_{11} = 4 \cdot 8 + 5 \cdot 10 + 6 \cdot 12 = 32 + 50 + 72 = 154$$

## Complexity

The triple loop performs exactly $m \cdot n \cdot k$ multiply-add operations,
so the time complexity is $\mathcal{O}(mnk)$.

For square matrices of size $n \times n$ this is $\mathcal{O}(n^3)$, which
becomes the bottleneck for large $n$. Real linear algebra libraries (BLAS,
cuBLAS) stay in the $\mathcal{O}(n^3)$ class algorithmically but achieve
much higher throughput through:

- **SIMD / vectorisation** — processing multiple elements per CPU cycle.
- **Cache blocking (tiling)** — reordering the loops so that data already in
  L1/L2 cache is reused before eviction.
- **Parallel execution** — distributing tile work across CPU cores or GPU
  streaming multiprocessors.

## Cache-Friendly Loop Order

In the naive implementation, the access pattern for $B$ is column-strided
(jumping by `n` elements for each increment of $p$), which causes frequent
cache misses for large matrices. The classic fix is to reorder the loops to
$i \to p \to j$:

```python
for i in range(m):
    for p in range(k):
        a_ip = A[i, p]          # loaded once per (i, p) pair
        for j in range(n):
            C[i, j] += a_ip * B[p, j]   # B[p, j] is now row-contiguous
```

This keeps both $B[p, \cdot]$ and $C[i, \cdot]$ in sequential (row-major)
order, dramatically improving spatial locality for large matrices.
