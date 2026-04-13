# Tensor Autograd Engine

## Your Task

In the previous problem you built an autograd engine for scalars. Now extend
the same idea to **tensors** (NumPy arrays), implementing a `Tensor` class
that tracks gradients through array operations.

This is the heart of how PyTorch's `autograd` works — a `Tensor` with
`requires_grad=True` records the operations applied to it, then replays
them in reverse during `backward()`.

### Fields

Each `Tensor` object must have:

- `data: np.ndarray` — the array value (always `dtype=float`)
- `grad: np.ndarray | None` — gradient of the output w.r.t. this tensor; `None` until `backward()` is called
- `requires_grad: bool` — whether to track gradients for this tensor
- `_backward: callable` — closure that propagates gradient from this node to its inputs
- `_prev: list` — parent `Tensor` objects in the computation graph

### Operations to implement

1. **`__add__(self, other)`** — elementwise addition with broadcasting support

   Backward: unbroadcast the gradient back to the original shape of each operand.

2. **`__mul__(self, other)`** — elementwise multiplication with broadcasting support

   Backward: $\frac{\partial L}{\partial A} = \frac{\partial L}{\partial C} \odot B$, unbroadcasted.

3. **`matmul(self, other)`** — matrix multiply: $C = A @ B$

   Backward: $\frac{\partial L}{\partial A} = \frac{\partial L}{\partial C} @ B^T$, $\quad\frac{\partial L}{\partial B} = A^T @ \frac{\partial L}{\partial C}$

4. **`sum(self)`** — sum all elements to a scalar `Tensor`

   Backward: broadcast `out.grad` back to the shape of `self`.

5. **`relu(self)`** — elementwise ReLU

   Backward: pass gradient through where input was positive, zero otherwise.

6. **`backward(self)`** — trigger the backward pass

   - Set `self.grad = np.ones_like(self.data)`
   - Build a topological ordering and call `_backward()` in reverse order

### Handling Broadcasting

When two arrays of different shapes are added or multiplied, NumPy broadcasts
the smaller one. To unbroadcast a gradient `g` back to shape `s`:

1. Sum over any leading dimensions that were added during broadcast
   (`while g.ndim > len(s): g = g.sum(axis=0)`).
2. Sum over any axis where `s` had size 1, keeping dims
   (`for axis, size in enumerate(s): if size == 1: g = g.sum(axis=axis, keepdims=True)`).

### Gradient accumulation

Use `+=` (not `=`) when accumulating into `.grad` so that tensors reused
in multiple branches of the graph receive contributions from all branches.

### Additional methods

- **`zero_grad(self)`** — reset `.grad` to `None`

## What to Print

Your `__main__` block should run two tests:

**Test 1 — matmul gradient**

```python
X = Tensor([[1, 2], [3, 4]], requires_grad=True)
W = Tensor([[0.1, 0.2], [0.3, 0.4]], requires_grad=True)
out = X.matmul(W)
loss = out.sum()
loss.backward()
```

Print `X.grad` and `W.grad` (rounded to 4 decimal places).

**Test 2 — ReLU gradient**

```python
A = Tensor([-1, 2, -3, 4], requires_grad=True)
B = A.relu().sum()
B.backward()
```

Print `A.grad` (rounded to 4 decimal places).

**Test 3 — numerical gradient checks**

Verify `X.grad` from Test 1 and `A.grad` from Test 2 using central differences.
Print the max absolute error for each — both should be below `1e-5`.

## Examples

```python
X = Tensor([[1, 2], [3, 4]], requires_grad=True)
W = Tensor([[0.1, 0.2], [0.3, 0.4]], requires_grad=True)
out = X.matmul(W)
loss = out.sum()
loss.backward()

# X.grad should be: out.grad @ W.T = ones(2x2) @ W.T
print(X.grad)
# [[0.3 0.7]
#  [0.3 0.7]]
```
