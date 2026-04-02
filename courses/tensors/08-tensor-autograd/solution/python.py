"""
Tensor Autograd with NumPy — Solution

A minimal autograd engine that wraps numpy arrays and supports:
  add, multiply, matmul, sum, relu — each with correct backward passes.
"""
import numpy as np


# ── Autograd engine ───────────────────────────────────────────────────────────

class Tensor:
    """A numpy array wrapper with automatic differentiation support."""

    def __init__(self, data, requires_grad=False):
        self.data = np.array(data, dtype=float)
        self.grad = None          # same shape as data; None until backward()
        self.requires_grad = requires_grad
        self._backward = lambda: None
        self._prev = []           # parent Tensors in the computation graph

    # ------------------------------------------------------------------
    # Forward operations
    # ------------------------------------------------------------------

    def __add__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data + other.data)
        out._prev = [self, other]

        def _backward():
            # Handle broadcasting: sum over any axes that were broadcast
            if self.requires_grad:
                grad = out.grad
                # Sum over leading broadcast dims
                while grad.ndim > self.data.ndim:
                    grad = grad.sum(axis=0)
                # Sum over axes where self had size 1
                for axis, size in enumerate(self.data.shape):
                    if size == 1:
                        grad = grad.sum(axis=axis, keepdims=True)
                self.grad = self.grad + grad if self.grad is not None else grad.copy()

            if other.requires_grad:
                grad = out.grad
                while grad.ndim > other.data.ndim:
                    grad = grad.sum(axis=0)
                for axis, size in enumerate(other.data.shape):
                    if size == 1:
                        grad = grad.sum(axis=axis, keepdims=True)
                other.grad = other.grad + grad if other.grad is not None else grad.copy()

        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data * other.data)
        out._prev = [self, other]

        def _backward():
            if self.requires_grad:
                g = other.data * out.grad
                while g.ndim > self.data.ndim:
                    g = g.sum(axis=0)
                for axis, size in enumerate(self.data.shape):
                    if size == 1:
                        g = g.sum(axis=axis, keepdims=True)
                self.grad = self.grad + g if self.grad is not None else g.copy()

            if other.requires_grad:
                g = self.data * out.grad
                while g.ndim > other.data.ndim:
                    g = g.sum(axis=0)
                for axis, size in enumerate(other.data.shape):
                    if size == 1:
                        g = g.sum(axis=axis, keepdims=True)
                other.grad = other.grad + g if other.grad is not None else g.copy()

        out._backward = _backward
        return out

    def matmul(self, other):
        """Matrix multiply: out = self @ other."""
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(np.matmul(self.data, other.data))
        out._prev = [self, other]

        def _backward():
            # if C = A @ B, then dL/dA = dL/dC @ B^T, dL/dB = A^T @ dL/dC
            if self.requires_grad:
                g = np.matmul(out.grad, other.data.T)
                self.grad = self.grad + g if self.grad is not None else g.copy()
            if other.requires_grad:
                g = np.matmul(self.data.T, out.grad)
                other.grad = other.grad + g if other.grad is not None else g.copy()

        out._backward = _backward
        return out

    def sum(self):
        """Sum all elements → scalar Tensor."""
        out = Tensor(self.data.sum())
        out._prev = [self]

        def _backward():
            if self.requires_grad:
                g = np.ones_like(self.data) * out.grad
                self.grad = self.grad + g if self.grad is not None else g.copy()

        out._backward = _backward
        return out

    def relu(self):
        """Elementwise ReLU."""
        out = Tensor(np.maximum(0, self.data))
        out._prev = [self]

        def _backward():
            if self.requires_grad:
                g = (self.data > 0).astype(float) * out.grad
                self.grad = self.grad + g if self.grad is not None else g.copy()

        out._backward = _backward
        return out

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

        self.grad = np.ones_like(self.data)
        for node in reversed(topo):
            node._backward()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def zero_grad(self):
        """Reset gradient to None."""
        self.grad = None

    def __repr__(self):
        return f"Tensor({self.data}, grad={self.grad})"


# ── Main block ────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # ── Test 1: matmul gradient ───────────────────────────────────────────────
    X = Tensor([[1, 2], [3, 4]], requires_grad=True)
    W = Tensor([[0.1, 0.2], [0.3, 0.4]], requires_grad=True)
    out = X.matmul(W)
    loss = out.sum()
    loss.backward()

    print("X.grad:")
    print(np.round(X.grad, 4))
    print("W.grad:")
    print(np.round(W.grad, 4))

    # ── Test 2: ReLU + sum ────────────────────────────────────────────────────
    A = Tensor([-1, 2, -3, 4], requires_grad=True)
    B = A.relu().sum()
    B.backward()
    print("A.grad (relu):", np.round(A.grad, 4))

    # ── Numerical gradient checks ─────────────────────────────────────────────
    def numerical_grad_matmul(eps=1e-5):
        """Check X.grad numerically for the matmul test."""
        errors = []
        X_data = np.array([[1.0, 2.0], [3.0, 4.0]])
        W_data = np.array([[0.1, 0.2], [0.3, 0.4]])

        analytic = np.round(np.matmul(np.ones((2, 2)), W_data.T), 4)  # dL/dX = ones @ W^T

        num_grad = np.zeros_like(X_data)
        for i in range(X_data.shape[0]):
            for j in range(X_data.shape[1]):
                Xp = X_data.copy(); Xp[i, j] += eps
                Xm = X_data.copy(); Xm[i, j] -= eps
                lp = np.matmul(Xp, W_data).sum()
                lm = np.matmul(Xm, W_data).sum()
                num_grad[i, j] = (lp - lm) / (2 * eps)

        return np.max(np.abs(num_grad - analytic))

    err_x = numerical_grad_matmul()
    print(f"Matmul X.grad check error: {err_x:.2e}")

    def numerical_grad_relu(eps=1e-5):
        A_data = np.array([-1.0, 2.0, -3.0, 4.0])
        analytic = np.array([0.0, 1.0, 0.0, 1.0])
        num_grad = np.zeros_like(A_data)
        for i in range(len(A_data)):
            Ap = A_data.copy(); Ap[i] += eps
            Am = A_data.copy(); Am[i] -= eps
            num_grad[i] = (np.maximum(0, Ap).sum() - np.maximum(0, Am).sum()) / (2 * eps)
        return np.max(np.abs(num_grad - analytic))

    err_a = numerical_grad_relu()
    print(f"ReLU A.grad check error: {err_a:.2e}")
