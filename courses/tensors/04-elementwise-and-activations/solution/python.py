"""
Element-wise Operations and Activation Functions — Solution
"""
import numpy as np


# ── Activation functions ─────────────────────────────────────────────────────

def relu(x: np.ndarray) -> np.ndarray:
    """ReLU: max(0, x) element-wise."""
    return np.maximum(0, x)


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Sigmoid: 1 / (1 + exp(-x)) element-wise."""
    return 1.0 / (1.0 + np.exp(-x))


def tanh(x: np.ndarray) -> np.ndarray:
    """Tanh: (exp(x) - exp(-x)) / (exp(x) + exp(-x)) element-wise."""
    ex  = np.exp(x)
    emx = np.exp(-x)
    return (ex - emx) / (ex + emx)


# ── Derivatives ──────────────────────────────────────────────────────────────

def relu_grad(x: np.ndarray) -> np.ndarray:
    """Derivative of ReLU: 1 where x > 0, else 0."""
    return (x > 0).astype(float)


def sigmoid_grad(x: np.ndarray) -> np.ndarray:
    """Derivative of sigmoid: sigmoid(x) * (1 - sigmoid(x))."""
    s = sigmoid(x)
    return s * (1.0 - s)


def tanh_grad(x: np.ndarray) -> np.ndarray:
    """Derivative of tanh: 1 - tanh(x)^2."""
    t = tanh(x)
    return 1.0 - t ** 2


# ── Main block ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])

    print("x          :", np.round(x, 4))
    print()
    print("relu       :", np.round(relu(x), 4))
    print("sigmoid    :", np.round(sigmoid(x), 4))
    print("tanh       :", np.round(tanh(x), 4))
    print()
    print("relu_grad  :", np.round(relu_grad(x), 4))
    print("sigmoid_grad:", np.round(sigmoid_grad(x), 4))
    print("tanh_grad  :", np.round(tanh_grad(x), 4))
    print()

    # Numerical gradient check for sigmoid
    h = 1e-5
    numerical = (sigmoid(x + h) - sigmoid(x - h)) / (2 * h)
    analytic  = sigmoid_grad(x)
    match = np.allclose(analytic, numerical, atol=1e-6)
    print("sigmoid gradient check passed:", match)
