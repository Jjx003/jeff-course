# Theory: Tensor Autograd

## From Scalars to Arrays

The scalar `Value` engine from the previous problem computed:

$$\frac{\partial L}{\partial x} \in \mathbb{R}$$

A tensor autograd engine computes the same thing, but now $x$ is a matrix
or vector, so the gradient has the **same shape** as $x$:

$$\frac{\partial L}{\partial X} \in \mathbb{R}^{m \times n} \quad \text{if } X \in \mathbb{R}^{m \times n}$$

The structure — computation graph, topological sort, `_backward` closures —
is identical. Only the local gradient rules change.

---

## Elementwise Operations

For $C = A + B$ (or $C = A \odot B$), every output element depends only on
the corresponding input elements, so the Jacobian is diagonal and the
backward rule is simple:

| Operation | Forward | Backward |
|-----------|---------|----------|
| $C = A + B$ | elementwise | $\dot A \mathrel{+}= \dot C$, $\dot B \mathrel{+}= \dot C$ |
| $C = A \odot B$ | elementwise | $\dot A \mathrel{+}= \dot C \odot B$, $\dot B \mathrel{+}= \dot C \odot A$ |
| $C = \text{ReLU}(A)$ | $\max(0, A)$ | $\dot A \mathrel{+}= \dot C \odot \mathbf{1}[A > 0]$ |

---

## Matrix Multiply

For $C = AB$ where $A \in \mathbb{R}^{m \times k}$ and $B \in \mathbb{R}^{k \times n}$:

$$\frac{\partial L}{\partial A} = \frac{\partial L}{\partial C} \cdot B^T \qquad \frac{\partial L}{\partial B} = A^T \cdot \frac{\partial L}{\partial C}$$

**Shape check** (always verify shapes):

| Quantity | Shape |
|----------|-------|
| $\dot C$ | $(m, n)$ |
| $B^T$ | $(n, k)$ |
| $\dot C \cdot B^T$ | $(m, k)$ ✓ same as $A$ |
| $A^T$ | $(k, m)$ |
| $A^T \cdot \dot C$ | $(k, n)$ ✓ same as $B$ |

---

## Sum

For a scalar $s = \sum_{i,j} A_{ij}$:

$$\frac{\partial L}{\partial A_{ij}} = \frac{\partial L}{\partial s} \cdot 1$$

So the backward pass broadcasts the scalar gradient `out.grad` to a matrix of
the same shape as `A`:

```python
g = np.ones_like(self.data) * out.grad
```

---

## Broadcasting and Unbroadcasting

NumPy broadcasting lets arrays of different shapes interact:

```python
A = np.ones((3, 4))   # shape (3, 4)
b = np.ones((4,))     # shape (4,) — broadcast over the 3 rows
C = A + b             # shape (3, 4)
```

During the forward pass, `b` was implicitly replicated 3 times. During the
backward pass, the gradient `dC` has shape `(3, 4)`, but we need to give
`b` a gradient of shape `(4,)`. The solution is to **sum over** the dimension
that was broadcast:

```python
db = dC.sum(axis=0)   # shape (4,) — sum over the replicated axis
```

General unbroadcast algorithm:
1. Sum over any leading dimensions added during broadcast (`g.ndim > original.ndim`).
2. Sum over any axis where `original` had size 1 (with `keepdims=True`).

---

## Reuse and Multi-Edge Gradients

Just as in the scalar engine, a tensor can be an input to multiple operations.
Each use contributes a gradient, so accumulate with `+=`:

```python
# a used twice: L = a.matmul(a)
# two gradient paths → both must add into a.grad
```

If you use `=` instead of `+=`, the second path overwrites the first and
the gradient is wrong.

---

## Connection to PyTorch

This engine is a faithful miniature of `torch.autograd`. The main differences
in PyTorch are:

- Operations are CUDA-accelerated and use fused kernels.
- Gradients can be detached (`tensor.detach()`) or left out (`requires_grad=False`).
- `retain_graph=True` allows calling `backward()` more than once.
- Higher-order gradients (Hessians) are supported.

But the fundamental design — `_backward` closures, topological sort, `+=`
accumulation — is exactly what you implemented here.
