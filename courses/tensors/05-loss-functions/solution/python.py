"""
Loss Functions and Their Gradients — Solution

Implements MSE loss, BCE loss, and their analytic gradients w.r.t. y_pred.
"""
import numpy as np


# ── Solution ─────────────────────────────────────────────────────────────────

def mse_loss(y_pred: np.ndarray, y_true: np.ndarray) -> float:
    """
    Mean Squared Error loss.

    L = (1/N) * sum((y_pred - y_true)^2)
    """
    return float(np.mean((y_pred - y_true) ** 2))


def mse_grad(y_pred: np.ndarray, y_true: np.ndarray) -> np.ndarray:
    """
    Gradient of MSE w.r.t. y_pred.

    dL/dy_pred = (2/N) * (y_pred - y_true)
    """
    N = len(y_pred)
    return (2.0 / N) * (y_pred - y_true)


def bce_loss(y_pred: np.ndarray, y_true: np.ndarray) -> float:
    """
    Binary Cross-Entropy loss.

    L = -(1/N) * sum(y_true*log(y_pred) + (1-y_true)*log(1-y_pred))
    Clips y_pred to [1e-7, 1-1e-7] for numerical stability.
    """
    eps = 1e-7
    y_pred_safe = np.clip(y_pred, eps, 1.0 - eps)
    return float(-np.mean(
        y_true * np.log(y_pred_safe) + (1.0 - y_true) * np.log(1.0 - y_pred_safe)
    ))


def bce_grad(y_pred: np.ndarray, y_true: np.ndarray) -> np.ndarray:
    """
    Gradient of BCE w.r.t. y_pred.

    dL/dy_pred = -(1/N) * (y_true/y_pred - (1-y_true)/(1-y_pred))
    Clips y_pred to [1e-7, 1-1e-7] before dividing.
    """
    eps = 1e-7
    N = len(y_pred)
    y_pred_safe = np.clip(y_pred, eps, 1.0 - eps)
    return -(1.0 / N) * (y_true / y_pred_safe - (1.0 - y_true) / (1.0 - y_pred_safe))


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
