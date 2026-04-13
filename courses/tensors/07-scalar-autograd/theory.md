# Theory: Scalar Autograd and Computation Graphs

## What is Autograd?

In the previous problem you derived gradients by hand and wrote them out
explicitly as matrix formulas. That works for a single fixed architecture,
but neural networks can have arbitrary structure — and rewriting gradients
by hand for every new model is impractical.

**Automatic differentiation** (autograd) solves this by recording what
operations were performed during the forward pass and then replaying them
in reverse to compute gradients.

---

## Computation Graphs

When you write `L = (a * b + c) ** 2`, you are implicitly constructing a
**directed acyclic graph** (DAG):

```
a ──┐
    ├─ mul ─→ t1 ──┐
b ──┘               ├─ add ─→ t2 ──── pow(2) ─→ L
c ──────────────────┘
```

Each node stores:
- Its **output value** (computed during the forward pass).
- A **`_backward` closure** that knows how to propagate gradients back to
  its inputs.
- References to its **parent nodes** (`_prev`).

---

## The Chain Rule, Mechanised

Backpropagation is just the chain rule applied systematically:

$$\frac{\partial L}{\partial x} = \frac{\partial L}{\partial z} \cdot \frac{\partial z}{\partial x}$$

For each operation $z = f(x, y)$, the `_backward` closure:
1. Reads the incoming gradient $\frac{\partial L}{\partial z}$ from `out.grad`.
2. Multiplies it by the **local** partial derivative $\frac{\partial z}{\partial x}$.
3. **Accumulates** the result into `x.grad` (using `+=`, not `=`, because a
   variable can appear in multiple places in the graph).

---

## Operation-by-Operation Backward Rules

| Operation | Forward | Backward |
|-----------|---------|----------|
| $z = x + y$ | $z = x + y$ | $\dot x \mathrel{+}= \dot z$, $\dot y \mathrel{+}= \dot z$ |
| $z = x \cdot y$ | $z = xy$ | $\dot x \mathrel{+}= y \cdot \dot z$, $\dot y \mathrel{+}= x \cdot \dot z$ |
| $z = x^n$ | $z = x^n$ | $\dot x \mathrel{+}= n x^{n-1} \cdot \dot z$ |
| $z = \text{ReLU}(x)$ | $z = \max(0,x)$ | $\dot x \mathrel{+}= \mathbf{1}[z>0] \cdot \dot z$ |

(Dot notation: $\dot z \equiv \frac{\partial L}{\partial z}$.)

---

## Topological Order

To apply the chain rule correctly, gradients must flow from **output toward
inputs** — i.e., a node must receive all incoming gradients before calling
`_backward`. Topological sort guarantees this: we process each node only
after all nodes that depend on it have already been processed.

A standard recursive DFS post-order traversal gives topological order:

```python
def build_topo(node):
    if node not in visited:
        visited.add(node)
        for parent in node._prev:
            build_topo(parent)
        topo.append(node)  # append AFTER recursing into parents
```

After building `topo`, iterate it in **reverse** to go from output to inputs.

---

## Why `+=` Not `=`

A variable can feed into multiple downstream nodes. For example if `a` is
used twice:

```python
L = a * a
```

The graph has two edges from `a` to the `mul` node. During backprop, `a.grad`
receives a contribution from each edge. Using `+=` ensures both contributions
are summed — this is the **multi-variate chain rule**.

---

## From Scalar to Tensor Autograd

This scalar engine is the exact conceptual foundation of PyTorch's autograd.
The only difference in practice is that PyTorch operates on tensors (arrays)
instead of scalars, and the local gradients become Jacobians or efficient
Jacobian-vector products. The graph structure and the `+=` accumulation rule
are identical.
