"""
Tensor Autograd Engine

Extend the scalar autograd idea to NumPy arrays. Implement a Tensor class
with forward operations and backward passes that correctly propagate gradients
through add, multiply, matmul, sum, and relu.
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
        """Elementwise addition with broadcasting support."""
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data + other.data)
        out._prev = [self, other]

        def _backward():
            # TODO: unbroadcast out.grad back to self.data.shape and other.data.shape
            # then accumulate into self.grad and other.grad
            pass

        out._backward = _backward
        return out

    def __mul__(self, other):
        """Elementwise multiplication with broadcasting support."""
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data * other.data)
        out._prev = [self, other]

        def _backward():
            # TODO: dL/dself = other.data * out.grad, unbroadcasted
            #       dL/dother = self.data * out.grad, unbroadcasted
            pass

        out._backward = _backward
        return out

    def matmul(self, other):
        """Matrix multiply: out = self @ other."""
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(np.matmul(self.data, other.data))
        out._prev = [self, other]

        def _backward():
            # TODO: if C = A @ B, then dL/dA = dL/dC @ B.T, dL/dB = A.T @ dL/dC
            pass

        out._backward = _backward
        return out

    def sum(self):
        """Sum all elements → scalar Tensor."""
        out = Tensor(self.data.sum())
        out._prev = [self]

        def _backward():
            # TODO: broadcast out.grad back to self.data.shape
            pass

        out._backward = _backward
        return out

    def relu(self):
        """Elementwise ReLU."""
        out = Tensor(np.maximum(0, self.data))
        out._prev = [self]

        def _backward():
            # TODO: pass gradient where input was positive, zero otherwise
            pass

        out._backward = _backward
        return out

    # ------------------------------------------------------------------
    # Backward pass
    # ------------------------------------------------------------------

    def backward(self):
        """Topological sort → call _backward in reverse order."""
        # TODO: build topological order and run backward pass
        raise NotImplementedError

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
        X_data = np.array([[1.0, 2.0], [3.0, 4.0]])
        W_data = np.array([[0.1, 0.2], [0.3, 0.4]])
        analytic = np.round(np.matmul(np.ones((2, 2)), W_data.T), 4)
        num_grad = np.zeros_like(X_data)
        for i in range(X_data.shape[0]):
            for j in range(X_data.shape[1]):
                Xp = X_data.copy(); Xp[i, j] += eps
                Xm = X_data.copy(); Xm[i, j] -= eps
                num_grad[i, j] = (np.matmul(Xp, W_data).sum() - np.matmul(Xm, W_data).sum()) / (2 * eps)
        return np.max(np.abs(num_grad - analytic))

    def numerical_grad_relu(eps=1e-5):
        A_data = np.array([-1.0, 2.0, -3.0, 4.0])
        analytic = np.array([0.0, 1.0, 0.0, 1.0])
        num_grad = np.zeros_like(A_data)
        for i in range(len(A_data)):
            Ap = A_data.copy(); Ap[i] += eps
            Am = A_data.copy(); Am[i] -= eps
            num_grad[i] = (np.maximum(0, Ap).sum() - np.maximum(0, Am).sum()) / (2 * eps)
        return np.max(np.abs(num_grad - analytic))

    print(f"Matmul X.grad check error: {numerical_grad_matmul():.2e}")
    print(f"ReLU A.grad check error: {numerical_grad_relu():.2e}")
