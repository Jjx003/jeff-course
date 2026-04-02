# Scalar Autograd Engine

## Your Task

Implement a `Value` class that wraps a scalar and can automatically compute
gradients by building a **computation graph** as you perform operations.

This is the core idea behind autograd engines like PyTorch's `torch.autograd`
— stripped down to its purest form.

### Fields

Each `Value` object must have:

- `data: float` — the scalar value
- `grad: float` — the gradient of the output with respect to this value (starts at `0.0`)
- `_backward: callable` — a closure that propagates gradient from this node to its inputs
- `_prev: set` — the set of `Value` objects that were inputs to this node

### Operations to implement

1. **`__add__(self, other)`** — addition: $z = x + y$

   Backward: $\frac{\partial L}{\partial x} \mathrel{+}= \frac{\partial L}{\partial z}$, same for $y$

2. **`__mul__(self, other)`** — multiplication: $z = x \cdot y$

   Backward: $\frac{\partial L}{\partial x} \mathrel{+}= y \cdot \frac{\partial L}{\partial z}$, $\quad\frac{\partial L}{\partial y} \mathrel{+}= x \cdot \frac{\partial L}{\partial z}$

3. **`__pow__(self, exp)`** — power by a plain number: $z = x^n$

   Backward: $\frac{\partial L}{\partial x} \mathrel{+}= n \cdot x^{n-1} \cdot \frac{\partial L}{\partial z}$

4. **`relu(self)`** — rectified linear unit: $z = \max(0, x)$

   Backward: $\frac{\partial L}{\partial x} \mathrel{+}= \mathbf{1}[z > 0] \cdot \frac{\partial L}{\partial z}$

5. **`backward(self)`** — trigger the backward pass from this node

   - Set `self.grad = 1.0` (the output's gradient w.r.t. itself)
   - Build a **topological ordering** of the computation graph
   - Call `_backward()` on each node in **reverse topological order**

Also implement these convenience wrappers using the primitives above:

- `__neg__` — negation: `-self`
- `__sub__` — subtraction: `self - other`
- `__truediv__` — division: `self / other`
- `__radd__` — right-hand add so `2 + Value(3)` works
- `__rmul__` — right-hand multiply so `2 * Value(3)` works

### Constraint

Wrap plain numbers automatically wherever `other` appears:

```python
other = other if isinstance(other, Value) else Value(other)
```

This lets you write expressions like `a * 2.0` without creating `Value(2.0)` manually.

## Examples

```python
# L = (a * b + c) ** 2
a = Value(2.0)
b = Value(-3.0)
c = Value(10.0)
L = (a * b + c) ** 2
L.backward()

print(f"L      = {L.data}")      # 16.0
print(f"a.grad = {a.grad}")      # -24.0
print(f"b.grad = {b.grad}")      # 16.0
print(f"c.grad = {c.grad}")      # 8.0
```

Work through the math by hand to verify:
- $a \cdot b = -6$, so $a \cdot b + c = 4$, so $L = 16$ ✓
- $\frac{\partial L}{\partial a} = 2(ab+c) \cdot b = 2 \cdot 4 \cdot (-3) = -24$ ✓

## What to print

Your `__main__` block should:

1. Compute `L = (a * b + c) ** 2` with `a=2.0, b=-3.0, c=10.0` and call `L.backward()`.
2. Print `L`, `a.grad`, `b.grad`, `c.grad`.
3. Run a **numerical gradient check** for each of `a`, `b`, `c` using the
   central-difference formula with $h = 10^{-5}$ and print the max absolute error
   — it should be below `1e-5`.
