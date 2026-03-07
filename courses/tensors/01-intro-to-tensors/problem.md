# Tensor Basics: Shape and Strides

## Your Task

Implement a minimal `Tensor` class that stores:

- `data` — a flat list of numbers (row-major / C-contiguous order)
- `shape` — a tuple describing the dimensions, e.g. `(3, 4)` for a 3×4 matrix
- `strides` — a tuple describing how many elements to skip per dimension

### Requirements

1. **Constructor** `Tensor(data, shape)` — accept a flat list and a shape tuple.
   Compute strides automatically (C-contiguous order).

2. **`__getitem__(indices)`** — support indexing like `t[1, 2]` using strides.

3. **`numel()`** — return the total number of elements.

4. **`__repr__()`** — return a readable string showing shape and first few values.

### Constraints

- Do **not** use NumPy or any external library.
- Strides are measured in **elements** (not bytes).
- Assume the data list length equals `math.prod(shape)`.

## Examples

```python
t = Tensor([1, 2, 3, 4, 5, 6], (2, 3))

print(t.shape)    # (2, 3)
print(t.strides)  # (3, 1)
print(t[0, 0])    # 1
print(t[1, 2])    # 6
print(t.numel())  # 6
```

For a shape `(2, 3)` the strides are `(3, 1)` because:

- Moving one step along axis 0 (rows) skips 3 elements.
- Moving one step along axis 1 (columns) skips 1 element.
