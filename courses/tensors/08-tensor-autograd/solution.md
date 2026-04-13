# Solution: Tensor Autograd Engine

## Key Ideas

### From scalars to arrays

The structure is identical to the scalar engine: every operation creates a new
`Tensor` and stores a `_backward` closure. The only new concern is shape.

### Matmul backward

For $C = A @ B$:

$$\frac{\partial L}{\partial A} = \frac{\partial L}{\partial C} \; B^T, \qquad
\frac{\partial L}{\partial B} = A^T \; \frac{\partial L}{\partial C}$$

In code:

```python
if self.requires_grad:
    self.grad = ... + np.matmul(out.grad, other.data.T)
if other.requires_grad:
    other.grad = ... + np.matmul(self.data.T, out.grad)
```

### Unbroadcasting for add and mul

When NumPy broadcasts two arrays, the gradient must be summed back over the
axes that were introduced or stretched:

```python
# 1. Sum over any leading axes that were broadcast in
while g.ndim > self.data.ndim:
    g = g.sum(axis=0)
# 2. Sum over axes where self had size 1
for axis, size in enumerate(self.data.shape):
    if size == 1:
        g = g.sum(axis=axis, keepdims=True)
```

### Sum backward

`sum()` reduces everything to a scalar. Its backward broadcasts the scalar
gradient back to every element:

```python
g = np.ones_like(self.data) * out.grad
```

### Gradient accumulation

Use `+=` (or `self.grad + g` if `self.grad` may be `None`):

```python
self.grad = self.grad + g if self.grad is not None else g.copy()
```

This is essential when the same tensor appears in multiple branches of the
computation graph.

## Common Mistakes

- **Using `=` instead of `+=`**: overwrites gradients from earlier branches,
  producing wrong results for any tensor used more than once.
- **Forgetting to unbroadcast**: if the backward of `add` or `mul` skips the
  unbroadcast step, the gradient shape will not match `self.data.shape` and NumPy
  will silently misalign accumulations.
- **Transposing the wrong operand in matmul**: the rules are asymmetric —
  `dL/dA` uses `B^T` on the right, while `dL/dB` uses `A^T` on the left.
- **Not checking `requires_grad`**: computing and storing a gradient for a tensor
  that does not need one wastes memory and can mask bugs; always guard with
  `if self.requires_grad`.
- **Initialising `self.grad = 1.0` instead of `np.ones_like`**: the scalar `1.0`
  will broadcast silently in simple cases but fail for multi-element tensors.
