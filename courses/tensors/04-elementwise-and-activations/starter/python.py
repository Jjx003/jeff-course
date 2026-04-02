"""
Element-wise Operations and Activation Functions

Implement six functions using NumPy:
  - relu, sigmoid, tanh          (the activations)
  - relu_grad, sigmoid_grad, tanh_grad  (their derivatives)

NumPy IS allowed for this and all subsequent problems.
"""
import numpy as np


# ── Activation functions ─────────────────────────────────────────────────────

def relu(x: np.ndarray) -> np.ndarray:
    """ReLU: max(0, x) element-wise."""
    # TODO: implement using np.maximum
    raise NotImplementedError


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Sigmoid: 1 / (1 + exp(-x)) element-wise."""
    # TODO: implement using np.exp
    raise NotImplementedError


def tanh(x: np.ndarray) -> np.ndarray:
    """Tanh: (exp(x) - exp(-x)) / (exp(x) + exp(-x)) element-wise.
    Implement using the exponential formula directly (not np.tanh).
    """
    # TODO: compute exp(x) and exp(-x), then combine
    raise NotImplementedError


# ── Derivatives ──────────────────────────────────────────────────────────────

def relu_grad(x: np.ndarray) -> np.ndarray:
    """Derivative of ReLU: 1 where x > 0, else 0."""
    # TODO: return a float array with 1.0 for x > 0, 0.0 elsewhere
    raise NotImplementedError


def sigmoid_grad(x: np.ndarray) -> np.ndarray:
    """Derivative of sigmoid: sigmoid(x) * (1 - sigmoid(x))."""
    # TODO: compute sigmoid(x) first, then use the formula
    raise NotImplementedError


def tanh_grad(x: np.ndarray) -> np.ndarray:
    """Derivative of tanh: 1 - tanh(x)^2."""
    # TODO: use your tanh function above
    raise NotImplementedError


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
