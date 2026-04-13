# Tips & Notes

## Start with `matmul` and `sum`

They are the cleanest to reason about and are the core of the main test.
Once `X.matmul(W).sum().backward()` gives correct gradients, add `relu`
and then `__add__`/`__mul__` with broadcasting.

## Shape Is Your Best Debugger

Before writing any backward code, write down the shape of every quantity:

```
C = A @ B    A:(m,k)  B:(k,n)  C:(m,n)
dL/dC: (m,n)
dL/dA = dL/dC @ B.T  →  (m,n)@(n,k) = (m,k) ✓
dL/dB = A.T @ dL/dC  →  (k,m)@(m,n) = (k,n) ✓
```

If a shape doesn't match the original parameter shape, you have the wrong
operand order.

## The Unbroadcast Helper

Extract unbroadcasting into a small helper — you'll use it in both `__add__`
and `__mul__`:

```python
def _unbroadcast(g, shape):
    while g.ndim > len(shape):
        g = g.sum(axis=0)
    for axis, size in enumerate(shape):
        if size == 1:
            g = g.sum(axis=axis, keepdims=True)
    return g
```

## Gradient Accumulation Pattern

Every `_backward` closure should follow this pattern:

```python
def _backward():
    if self.requires_grad:
        g = ...compute local gradient...
        self.grad = self.grad + g if self.grad is not None else g.copy()
```

Using `g.copy()` for the first assignment avoids aliasing bugs where
modifying `out.grad` later would corrupt `self.grad`.

## `requires_grad` Guard

Only compute and accumulate a gradient if the operand actually needs one:

```python
if self.requires_grad:
    ...
if other.requires_grad:
    ...
```

This mirrors how PyTorch skips gradient computation for frozen layers.

## Numerical Gradient Check Recipe

```python
def numerical_grad(fn, tensor, eps=1e-5):
    grad = np.zeros_like(tensor.data)
    it = np.nditer(tensor.data, flags=['multi_index'])
    while not it.finished:
        idx = it.multi_index
        orig = tensor.data[idx]
        tensor.data[idx] = orig + eps; fp = fn()
        tensor.data[idx] = orig - eps; fm = fn()
        tensor.data[idx] = orig
        grad[idx] = (fp - fm) / (2 * eps)
        it.iternext()
    return grad
```

Compare with analytic gradient using `np.max(np.abs(num - analytic))`.
Values below `1e-5` confirm correctness.

## Common Bugs

- **Missing `requires_grad` check**: gradients accumulate into leaf tensors
  that never needed them, causing shape errors later.
- **Wrong transpose**: `dL/dA = dL/dC @ B.T` not `B @ dL/dC`. Check shapes.
- **Broadcasting not unbroadcasted**: if operands had different shapes,
  the gradient must be summed back to the original shape before accumulating.
- **`=` instead of `+=`**: breaks multi-use tensors silently.
