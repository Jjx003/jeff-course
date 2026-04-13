# Tips & Notes

## Start with `__add__` and `__mul__`

These two operations are the core. Get them right first — the others follow
the same pattern. Once `backward()` works for `a * b + c`, you can add
`__pow__` and `relu` one at a time.

## The `+=` Rule Is Non-Negotiable

Always accumulate gradients with `+=`, never `=`. If a value is used in
multiple places in the expression (e.g., `a * a`), both uses must add their
gradient contribution. Overwriting with `=` silently drops one of them.

## Wrap Plain Numbers Early

Add this to every binary operation:

```python
other = other if isinstance(other, Value) else Value(other)
```

Without it, `a * 2.0` will crash. With it, expressions like `a * 2.0 + 1.0`
work seamlessly.

## Check Topological Order Visually

For `L = (a * b + c) ** 2`, the expected topo order (before reversal) is:

```
a, b, (a*b), c, (a*b+c), L
```

Reversed: `L, (a*b+c), (a*b), c, b, a`. Printing each node as you call
`_backward()` helps confirm you have the right order.

## Implement Convenience Wrappers Last

`__neg__`, `__sub__`, `__truediv__`, `__radd__`, `__rmul__` are all one-liners
once the primitives work. For example:

```python
def __neg__(self):   return self * -1
def __sub__(self, other): return self + (-other)
def __truediv__(self, other): return self * other**-1
```

## Numerical Gradient Check

The central-difference formula gives a reliable sanity check:

$$\frac{\partial L}{\partial x} \approx \frac{L(x+h) - L(x-h)}{2h}, \quad h = 10^{-5}$$

If your analytic gradient matches to within `1e-5`, the backward pass is
correct. If the error is large, the most common culprits are:

- Forgetting `+=` (using `=` instead).
- Wrong sign in a backward rule.
- Missing `self.data` dereference inside a closure (Python captures variables
  by reference — use `self.data` at closure-definition time, not a local alias
  that may change).

## Common Closure Bug

This is a subtle Python gotcha:

```python
# BUG: 'exp' is captured by reference — always reads the last value of exp
def __pow__(self, exp):
    out = Value(self.data ** exp, (self,))
    def _backward():
        self.grad += exp * ...   # 'exp' here refers to the enclosing scope
    out._backward = _backward
    return out
```

In this case it's fine because `exp` is a parameter. But if you ever use a
loop variable inside a closure, capture it explicitly:
`lambda x=x: ...` or assign to a local name inside the function.

## Next Steps

After this problem you will extend the same idea to tensors, replacing
scalar `.data` with NumPy arrays and scalar gradients with arrays of the
same shape.
