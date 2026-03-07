# Tips & Notes

## Computing Strides

Work from the **last** dimension backwards. The last stride is always 1 (elements are adjacent).
Each earlier stride is the product of all later dimension sizes.

```python
def compute_strides(shape):
    strides = [1] * len(shape)
    for i in range(len(shape) - 2, -1, -1):
        strides[i] = strides[i + 1] * shape[i + 1]
    return tuple(strides)
```

## Flat Offset from Multi-Index

```python
def flat_index(indices, strides):
    return sum(i * s for i, s in zip(indices, strides))
```

## Common Pitfalls

- **Shape mismatch**: `math.prod(shape)` must equal `len(data)`. Add an assertion.
- **Negative indices**: For this exercise, you can ignore negative indices — but note
  that NumPy supports them.
- **Scalar tensors**: shape `()` has strides `()` and numel `1`. Treat as a special case
  if needed.

## Checking Your Work

```python
import math

t = Tensor(list(range(24)), (2, 3, 4))
assert t.strides == (12, 4, 1)
assert t[1, 2, 3] == 23   # last element
assert t.numel() == 24
```

## Next Steps

Once your basic tensor works, try:
- Implement a `reshape(new_shape)` method (validate that numel is preserved).
- Implement `transpose()` for 2-D tensors by swapping shape and strides.
