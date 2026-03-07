# Tips & Notes

## broadcast_shapes step-by-step

```python
def broadcast_shapes(a, b):
    # 1. Right-align by padding shorter shape with 1s on the left
    ndim = max(len(a), len(b))
    a = (1,) * (ndim - len(a)) + tuple(a)
    b = (1,) * (ndim - len(b)) + tuple(b)

    # 2. Compute output size per dimension
    out = []
    for sa, sb in zip(a, b):
        if sa == sb:
            out.append(sa)
        elif sa == 1:
            out.append(sb)
        elif sb == 1:
            out.append(sa)
        else:
            raise ValueError(f"Shapes {a} and {b} are not broadcastable")
    return tuple(out)
```

## Iterating Over All Output Indices

Use `itertools.product` to visit every multi-index in the output:

```python
import itertools

out_shape = broadcast_shapes(A.shape, B.shape)
result = [0.0] * math.prod(out_shape)
C = Tensor(result, out_shape)

for idx in itertools.product(*[range(d) for d in out_shape]):
    # Clamp each index for A and B:
    idx_a = tuple(min(i, sa - 1) for i, sa in zip(idx, padded_shape_a))
    idx_b = tuple(min(i, sb - 1) for i, sb in zip(idx, padded_shape_b))
    C[idx] = A[idx_a] + B[idx_b]
```

## Common Mistakes

- Forgetting to pad shapes with leading `1`s before comparing.
- Off-by-one: clamping should use `size - 1`, not `size`.
- Mutating the input shapes — work on copies.

## Testing Corner Cases

```python
# Same shape — no broadcasting needed
assert broadcast_shapes((3, 4), (3, 4)) == (3, 4)

# Scalar (size-1 in all dims)
assert broadcast_shapes((1,), (5,)) == (5,)

# Leading dim expansion
assert broadcast_shapes((4, 1), (3,)) == (4, 3)

# Incompatible
try:
    broadcast_shapes((3,), (2,))
    assert False, "Should have raised"
except ValueError:
    pass
```
