"""
Scalar Autograd Engine

Implement a Value class that wraps a scalar and automatically computes
gradients by building a computation graph during the forward pass.
"""


# ── Your implementation ──────────────────────────────────────────────────────

class Value:
    """A scalar value with automatic differentiation support."""

    def __init__(self, data, _children=()):
        self.data = float(data)
        self.grad = 0.0
        self._backward = lambda: None   # closure: propagates grad to inputs
        self._prev = set(_children)     # parent Values in the computation graph

    # ------------------------------------------------------------------
    # Forward operations — each must set out._backward
    # ------------------------------------------------------------------

    def __add__(self, other):
        """z = self + other.  dL/dself += dL/dz, dL/dother += dL/dz."""
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other))

        def _backward():
            # TODO: accumulate gradient into self.grad and other.grad
            pass

        out._backward = _backward
        return out

    def __mul__(self, other):
        """z = self * other.  dL/dself += other * dL/dz, dL/dother += self * dL/dz."""
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other))

        def _backward():
            # TODO: accumulate gradient into self.grad and other.grad
            pass

        out._backward = _backward
        return out

    def __pow__(self, exp):
        """z = self ** exp.  dL/dself += exp * self^(exp-1) * dL/dz."""
        assert isinstance(exp, (int, float)), "exponent must be a plain number"
        out = Value(self.data ** exp, (self,))

        def _backward():
            # TODO: accumulate gradient into self.grad
            pass

        out._backward = _backward
        return out

    def relu(self):
        """z = max(0, self).  dL/dself += (z > 0) * dL/dz."""
        out = Value(max(0, self.data), (self,))

        def _backward():
            # TODO: accumulate gradient into self.grad
            pass

        out._backward = _backward
        return out

    # ------------------------------------------------------------------
    # Convenience wrappers — implement using the primitives above
    # ------------------------------------------------------------------

    def __neg__(self):
        # TODO: return -self using __mul__
        raise NotImplementedError

    def __sub__(self, other):
        # TODO: return self - other using __add__ and __neg__
        raise NotImplementedError

    def __truediv__(self, other):
        # TODO: return self / other using __mul__ and __pow__
        raise NotImplementedError

    def __radd__(self, other):
        return self + other

    def __rmul__(self, other):
        return self * other

    # ------------------------------------------------------------------
    # Backward pass
    # ------------------------------------------------------------------

    def backward(self):
        """
        Trigger the backward pass from this node.

        Steps:
        1. Build a topological ordering of the computation graph.
        2. Set self.grad = 1.0.
        3. Call _backward() on each node in reverse topological order.
        """
        # TODO: implement topological sort and backward pass
        raise NotImplementedError

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
    errors = []
    for idx, pos in enumerate([0, 1, 2]):
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
