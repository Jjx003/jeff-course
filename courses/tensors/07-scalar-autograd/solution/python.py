"""
Scalar Autograd Engine — Solution

A minimal autograd engine that wraps scalars and computes gradients
automatically by building a computation graph during the forward pass.
"""


# ── Autograd engine ───────────────────────────────────────────────────────────

class Value:
    """A scalar value with automatic differentiation support."""

    def __init__(self, data, _children=()):
        self.data = float(data)
        self.grad = 0.0
        self._backward = lambda: None
        self._prev = set(_children)

    # ------------------------------------------------------------------
    # Forward operations
    # ------------------------------------------------------------------

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other))

        def _backward():
            self.grad += out.grad
            other.grad += out.grad

        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other))

        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad

        out._backward = _backward
        return out

    def __pow__(self, exp):
        assert isinstance(exp, (int, float)), "exponent must be a plain number"
        out = Value(self.data ** exp, (self,))

        def _backward():
            self.grad += exp * (self.data ** (exp - 1)) * out.grad

        out._backward = _backward
        return out

    def relu(self):
        out = Value(max(0, self.data), (self,))

        def _backward():
            self.grad += (out.data > 0) * out.grad

        out._backward = _backward
        return out

    # ------------------------------------------------------------------
    # Convenience wrappers
    # ------------------------------------------------------------------

    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + (-other)

    def __truediv__(self, other):
        return self * other ** -1

    def __radd__(self, other):
        return self + other

    def __rmul__(self, other):
        return self * other

    # ------------------------------------------------------------------
    # Backward pass
    # ------------------------------------------------------------------

    def backward(self):
        """Topological sort → call _backward in reverse order."""
        topo = []
        visited = set()

        def build_topo(node):
            if id(node) not in visited:
                visited.add(id(node))
                for parent in node._prev:
                    build_topo(parent)
                topo.append(node)

        build_topo(self)

        self.grad = 1.0
        for node in reversed(topo):
            node._backward()

    def __repr__(self):
        return f"Value(data={self.data}, grad={self.grad})"


# ── Main block ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # L = (a * b + c) ** 2
    a = Value(2.0)
    b = Value(-3.0)
    c = Value(10.0)
    L = (a * b + c) ** 2
    L.backward()

    print(f"L      = {L.data}")
    print(f"a.grad = {a.grad}")
    print(f"b.grad = {b.grad}")
    print(f"c.grad = {c.grad}")

    # Numerical gradient check
    def numerical_grad(fn, val, h=1e-5):
        orig = val.data
        val.data = orig + h
        fp = fn()
        val.data = orig - h
        fm = fn()
        val.data = orig
        return (fp - fm) / (2 * h)

    def forward():
        aa = Value(2.0); bb = Value(-3.0); cc = Value(10.0)
        return (aa * bb + cc) ** 2, aa, bb, cc

    errors = []
    for idx, (name, pos) in enumerate([("a", 0), ("b", 1), ("c", 2)]):
        h = 1e-5
        vals = [2.0, -3.0, 10.0]
        vp = [Value(v) for v in vals]; vp[pos].data += h
        vm = [Value(v) for v in vals]; vm[pos].data -= h
        fp = (vp[0] * vp[1] + vp[2]) ** 2
        fm = (vm[0] * vm[1] + vm[2]) ** 2
        num = (fp.data - fm.data) / (2 * h)
        analytic = [a.grad, b.grad, c.grad][idx]
        errors.append(abs(num - analytic))

    print(f"Max numerical gradient error: {max(errors):.2e}")
