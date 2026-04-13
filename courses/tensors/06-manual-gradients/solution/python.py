"""
Manual Gradients: Linear Regression — Solution

Implements forward pass, MSE loss, manual backward pass, and SGD for a
1-layer linear regression model trained on a toy dataset.
"""
import numpy as np


# ── Solution ─────────────────────────────────────────────────────────────────

def linear_forward(X: np.ndarray, W: np.ndarray, b: np.ndarray) -> np.ndarray:
    """y_pred = X @ W + b, shape (N, 1)."""
    return X @ W + b


def mse_loss(y_pred: np.ndarray, y: np.ndarray) -> float:
    """Mean Squared Error: (1/N) * sum((y_pred - y)^2)."""
    return float(np.mean((y_pred - y) ** 2))


def linear_backward(dL_dy_pred: np.ndarray, X: np.ndarray, W: np.ndarray):
    """
    Backprop through y_pred = X @ W + b.

    Returns (dL_dW, dL_db, dL_dX).
    """
    dL_dW = X.T @ dL_dy_pred          # (D, 1)
    dL_db = float(dL_dy_pred.sum())   # scalar
    dL_dX = dL_dy_pred @ W.T          # (N, D)
    return dL_dW, dL_db, dL_dX


def sgd_step(W: np.ndarray, b: np.ndarray,
             dL_dW: np.ndarray, dL_db: float, lr: float) -> None:
    """Gradient descent update (in-place)."""
    W -= lr * dL_dW
    b -= lr * dL_db


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Dataset
    np.random.seed(42)
    N, D = 50, 2
    X = np.random.randn(N, D)
    true_W = np.array([[2.0], [-1.0]])
    true_b = np.array([0.5])
    noise = 0.1 * np.random.randn(N, 1)
    y = X @ true_W + true_b + noise

    # Parameters
    np.random.seed(42)
    W = np.random.randn(D, 1)
    b = np.zeros(1)

    lr = 0.1

    for step in range(100):
        # Forward
        y_pred = linear_forward(X, W, b)
        loss = mse_loss(y_pred, y)

        if step in (0, 50, 99):
            print(f"Step {step:3d} | loss: {loss:.4f}")

        # Backward
        dL_dy_pred = (2 / N) * (y_pred - y)
        dL_dW, dL_db, _ = linear_backward(dL_dy_pred, X, W)

        # Update
        sgd_step(W, b, dL_dW, dL_db, lr)

    print(f"Final W: {np.round(W.flatten(), 4)}")
    print(f"Final b: {np.round(b, 4)}")
