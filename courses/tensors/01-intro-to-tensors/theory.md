# Theory: What is a Tensor?

A **tensor** is a multi-dimensional array of numbers. It generalises:

| Name     | Rank | Shape example |
|----------|------|---------------|
| Scalar   | 0    | `()`          |
| Vector   | 1    | `(n,)`        |
| Matrix   | 2    | `(m, n)`      |
| 3-tensor | 3    | `(b, m, n)`   |

In deep learning, a "batch of images" is a 4-D tensor with shape `(batch, channels, height, width)`.

---

## Memory Layout

A tensor's data lives in a **flat, contiguous block of memory**.
The *shape* and *strides* tell us how to interpret that flat array as a multi-dimensional structure.

### Strides

For a tensor with shape $(d_0, d_1, \ldots, d_{k-1})$, the **C-contiguous strides** are:

$$s_i = \prod_{j=i+1}^{k-1} d_j$$

For example, shape $(2, 3, 4)$ gives strides $(12, 4, 1)$.

To access element at index $(i_0, i_1, \ldots, i_{k-1})$, compute the flat offset:

$$\text{offset} = \sum_{j=0}^{k-1} i_j \cdot s_j$$

### Why Strides Matter

Strides make **zero-copy views** possible. A transpose, reshape, or slice can
return a new tensor that shares the same underlying data but has different strides —
no memory is copied. This is how NumPy and PyTorch achieve efficiency.

```
data = [1, 2, 3, 4, 5, 6]

shape=(2,3), strides=(3,1)   →  [[1, 2, 3],
                                  [4, 5, 6]]

shape=(3,2), strides=(2,1)   →  [[1, 2],    (reshape, same data)
                                  [3, 4],
                                  [5, 6]]

Transposed: shape=(2,3)→(3,2), strides=(3,1)→(1,3)
```

---

## C-order vs F-order

- **C-order (row-major)**: last axis varies fastest. Default for NumPy, PyTorch.
- **F-order (column-major)**: first axis varies fastest. Default for MATLAB, Fortran.

This course uses C-order throughout.
