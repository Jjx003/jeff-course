# Solution: Tensor Basics — Shape and Strides

## Key Insight

The core of this problem is understanding **C-contiguous (row-major) strides**: for a tensor with shape $(d_0, d_1, \ldots, d_{n-1})$, the stride for dimension $i$ is the product of all dimension sizes that come *after* it:

$$s_i = \prod_{j=i+1}^{n-1} d_j$$

This tells you: "to move one step along dimension $i$, how many elements do you skip in the flat array?"

## Computing Strides

Start from the last dimension (stride = 1) and work backwards:

```python
def _compute_strides(self, shape):
    strides = []
    stride = 1
    for dim in reversed(shape):
        strides.append(stride)
        stride *= dim
    return tuple(reversed(strides))
```

For shape `(2, 3)`:
- Last dim (size 3): stride = 1 → moving along columns costs 1 element
- First dim (size 2): stride = 3 → moving along rows costs 3 elements
- Result: `(3, 1)` ✓

## Indexing with Strides

Once you have strides, indexing is just a dot product:

```python
def __getitem__(self, indices):
    if isinstance(indices, int):
        indices = (indices,)
    offset = sum(i * s for i, s in zip(indices, self.strides))
    return self.data[offset]
```

For `t[1, 2]` with strides `(3, 1)`: offset = 1×3 + 2×1 = 5 → `data[5]` = 6 ✓

## Why This Matters

This stride-based design is exactly how NumPy and PyTorch work internally. It enables:
- **Views** (slices that share memory with the original)
- **Transposition** (just swap strides, no data copy)
- **Broadcasting** (set stride to 0 for broadcast dimensions)
