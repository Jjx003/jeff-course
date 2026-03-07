# Matrix Multiplication

## Your Task

Implement `matmul(A, B)` that multiplies two 2-D `Tensor` objects.

### Requirements

1. **`matmul(A, B) -> Tensor`**
   - `A` has shape `(m, k)`, `B` has shape `(k, n)`.
   - Return a new `Tensor` with shape `(m, n)`.
   - Raise a `ValueError` if the inner dimensions don't match.

2. **Naive triple loop** first — correctness over speed.

3. **Optional bonus**: implement a cache-friendly version by reordering loops
   to improve L1 cache utilisation.

### Constraints

- Build on top of your `Tensor` from problem 1.
- Do **not** use NumPy or any BLAS library.

## Examples

```python
A = Tensor([1, 2, 3, 4, 5, 6], (2, 3))
B = Tensor([7, 8, 9, 10, 11, 12], (3, 2))

C = matmul(A, B)
# C.shape == (2, 2)
# C[0,0] = 1*7 + 2*9  + 3*11 = 58
# C[0,1] = 1*8 + 2*10 + 3*12 = 64
# C[1,0] = 4*7 + 5*9  + 6*11 = 139
# C[1,1] = 4*8 + 5*10 + 6*12 = 154
print(C[0, 0])  # 58
print(C[1, 1])  # 154
```

## Performance Note

The naive triple loop is $O(mnk)$. For square matrices of size $n$:

$$\text{FLOPs} = 2n^3$$

(One multiply + one add per element of A×B, repeated for every output cell.)
For `n = 1024`, that's ~2 billion FLOPs — optimised BLAS routines achieve this
in milliseconds using SIMD and cache blocking.
