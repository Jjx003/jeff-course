"""
Loss Functions and Their Gradients

Implement MSE loss, BCE loss, and their analytic gradients w.r.t. y_pred.
NumPy is available and encouraged.
"""
import numpy as np


# ── Your implementation ──────────────────────────────────────────────────────

def mse_loss(y_pred: np.ndarray, y_true: np.ndarray) -> float:
    """
    Mean Squared Error loss.

    Args:
        y_pred: predicted values, shape (N,)
        y_true: ground-truth values, shape (N,)

    Returns:
        Scalar loss: (1/N) * sum((y_pred - y_true)^2)
    """
    # TODO: implement
    raise NotImplementedError


def mse_grad(y_pred: np.ndarray, y_true: np.ndarray) -> np.ndarray:
    """
    Gradient of MSE loss w.r.t. y_pred.

    Returns:
        Array of shape (N,): (2/N) * (y_pred - y_true)
    """
    # TODO: implement
    raise NotImplementedError


def bce_loss(y_pred: np.ndarray, y_true: np.ndarray) -> float:
    """
    Binary Cross-Entropy loss.

    Clips y_pred to [1e-7, 1-1e-7] before taking logs.

    Args:
        y_pred: predicted probabilities in (0, 1), shape (N,)
        y_true: binary labels in {0, 1}, shape (N,)

    Returns:
        Scalar loss: -(1/N) * sum(y_true*log(y_pred) + (1-y_true)*log(1-y_pred))
    """
    # TODO: clip y_pred, then implement
    raise NotImplementedError


def bce_grad(y_pred: np.ndarray, y_true: np.ndarray) -> np.ndarray:
    """
    Gradient of BCE loss w.r.t. y_pred.

    Clips y_pred to [1e-7, 1-1e-7] before dividing.

    Returns:
        Array of shape (N,): -(1/N) * (y_true/y_pred - (1-y_true)/(1-y_pred))
    """
    # TODO: clip y_pred, then implement
    raise NotImplementedError


# ── Smoke tests ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    y_pred = np.array([0.9, 0.2, 0.8, 0.4])
    y_true = np.array([1.0, 0.0, 1.0, 0.0])

    # MSE
    print("MSE loss:    ", round(mse_loss(y_pred, y_true), 4))
    print("MSE gradient:", mse_grad(y_pred, y_true).round(4))

    # BCE
    print("BCE loss:    ", round(bce_loss(y_pred, y_true), 4))
    print("BCE gradient:", bce_grad(y_pred, y_true).round(4))

    # Numerical gradient check
    def numerical_grad(loss_fn, y_pred, y_true, eps=1e-5):
        grad = np.zeros_like(y_pred)
        for i in range(len(y_pred)):
            yp = y_pred.copy(); yp[i] += eps
            ym = y_pred.copy(); ym[i] -= eps
            grad[i] = (loss_fn(yp, y_true) - loss_fn(ym, y_true)) / (2 * eps)
        return grad

    mse_num = numerical_grad(mse_loss, y_pred, y_true)
    bce_num = numerical_grad(bce_loss, y_pred, y_true)

    print("MSE grad check error:", f"{np.max(np.abs(mse_num - mse_grad(y_pred, y_true))):.2e}")
    print("BCE grad check error:", f"{np.max(np.abs(bce_num - bce_grad(y_pred, y_true))):.2e}")
