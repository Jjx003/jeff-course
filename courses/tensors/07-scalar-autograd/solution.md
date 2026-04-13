# Solution: Scalar Autograd Engine

## Key Ideas

### Building the graph during the forward pass

Every operation creates a new `Value` and captures the inputs in `_prev`:

```python
out = Value(self.data + other.data, (self, other))
```

The `_backward` closure stores references to the *input* nodes (not copies of
their data), so when it runs later it writes gradients directly into the right
objects.

### Gradient accumulation with `+=`

Every `_backward` uses `+=`, never `=`:

```python
self.grad += out.grad
```

A node can appear in multiple branches (e.g. `a * a`). Each branch contributes
its own partial gradient, so you must *add* rather than *overwrite*.

### Topological sort for the backward pass

`backward()` builds a topological ordering by post-order DFS, then iterates in
reverse:

```python
self.grad = 1.0
for node in reversed(topo):
    node._backward()
```

Reversed post-order guarantees that every node's `_backward` runs only after all
nodes that depend on it have already accumulated their gradients.

### Power rule and convenience wrappers

`__pow__` covers `x**n` for any scalar exponent. The convenience wrappers
(`__neg__`, `__sub__`, `__truediv__`, `__radd__`, `__rmul__`) compose these
primitives rather than implementing new backward passes, which keeps the engine
minimal and correct by construction.

## Common Mistakes

- **Using `=` instead of `+=` in `_backward`**: causes wrong gradients whenever a
  node is used more than once in the graph.
- **Forgetting `self.grad = 1.0` at the start of `backward()`**: without seeding
  the output gradient, all computed gradients are 0.
- **Visiting the same node twice in `build_topo`**: guard with a `visited` set
  checked on `id(node)`, not on the node itself (objects are not hashable by value).
- **Wrong sign in power rule**: `exp * (self.data ** (exp - 1))` — the exponent
  moves in front and decrements by 1.
