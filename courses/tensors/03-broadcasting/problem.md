# Broadcasting

## Your Task

Implement `broadcast_add(A, B)` that adds two tensors with broadcasting.

### Broadcasting Rules (NumPy-compatible)

Shapes are compared **right-aligned**. For each dimension pair:

1. If the sizes are equal → keep that size.
2. If one size is `1` → stretch it to match the other.
3. If both are `> 1` and unequal → raise a `ValueError`.
4. Missing leading dimensions are treated as size `1`.

### Requirements

1. **`broadcast_shapes(shape_a, shape_b) -> Tuple`**
   Return the output shape after applying broadcasting rules.
   Raise `ValueError` for incompatible shapes.

2. **`broadcast_add(A, B) -> Tensor`**
   Add `A` and `B` element-wise with broadcasting.
   Return a new `Tensor` with the broadcast shape.

### Constraints

- No NumPy.
- Support tensors of any rank.

## Examples

```python
# Scalar broadcast
a = Tensor([1, 2, 3], (3,))
b = Tensor([10], (1,))
c = broadcast_add(a, b)  # shape (3,): [11, 12, 13]

# Row vector + column vector → matrix
row = Tensor([1, 2, 3], (1, 3))
col = Tensor([10, 20], (2, 1))
out = broadcast_add(row, col)
# shape (2, 3):
# [[11, 12, 13],
#  [21, 22, 23]]

# Shape mismatch
x = Tensor([1, 2, 3], (3,))
y = Tensor([1, 2], (2,))
broadcast_add(x, y)  # raises ValueError
```
