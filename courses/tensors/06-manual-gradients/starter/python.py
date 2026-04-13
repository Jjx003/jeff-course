"""
Manual Gradients: Linear Regression

Implement the forward pass, MSE loss, manual backward pass, and SGD step
for a 1-layer linear regression model, then train it on a toy dataset.
NumPy is available and encouraged.
"""
import numpy as np


# ── Your implementation ──────────────────────────────────────────────────────

def linear_forward(X: np.ndarray, W: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Compute linear predictions: y_pred = X @ W + b.

    Args:
        X: input, shape (N, D)
        W: weights, shape (D, 1)
        b: bias, shape (1,)

    Returns:
        y_pred: shape (N, 1)
    """
    # TODO: implement
    raise NotImplementedError


def mse_loss(y_pred: np.ndarray, y: np.ndarray) -> float:
    """
    Mean Squared Error: (1/N) * sum((y_pred - y)^2).

    Args:
        y_pred: predictions, shape (N, 1)
        y:      targets,     shape (N, 1)

    Returns:
        Scalar loss value.
    """
    # TODO: implement
    raise NotImplementedError


def linear_backward(dL_dy_pred: np.ndarray, X: np.ndarray, W: np.ndarray):
    """
    Backprop through y_pred = X @ W + b.

    Args:
        dL_dy_pred: upstream gradient, shape (N, 1)
        X:          input, shape (N, D)
        W:          weights, shape (D, 1)

    Returns:
        (dL_dW, dL_db, dL_dX)
          dL_dW: shape (D, 1)
          dL_db: scalar
          dL_dX: shape (N, D)
    """
    # TODO: implement
    # Hint: dL_dW = X.T @ dL_dy_pred
    #       dL_db = dL_dy_pred.sum()
    #       dL_dX = dL_dy_pred @ W.T
    raise NotImplementedError


def sgd_step(W: np.ndarray, b: np.ndarray,
             dL_dW: np.ndarray, dL_db: float, lr: float) -> None:
    """
    In-place gradient descent update.

    Args:
        W:     weights, shape (D, 1)
        b:     bias, shape (1,)
        dL_dW: weight gradient, shape (D, 1)
        dL_db: bias gradient, scalar
        lr:    learning rate
    """
    # TODO: implement (update W and b in-place)
    raise NotImplementedError


# ── Training loop ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Generate toy dataset
    np.random.seed(42)
    N, D = 50, 2
    X = np.random.randn(N, D)
    true_W = np.array([[2.0], [-1.0]])
    true_b = np.array([0.5])
    noise = 0.1 * np.random.randn(N, 1)
    y = X @ true_W + true_b + noise

    # Initialise parameters
    np.random.seed(42)
    W = np.random.randn(D, 1)
    b = np.zeros(1)

    lr = 0.1

    for step in range(100):
        # Forward pass
        y_pred = linear_forward(X, W, b)
        loss = mse_loss(y_pred, y)

        if step in (0, 50, 99):
            print(f"Step {step:3d} | loss: {loss:.4f}")

        # Backward pass
        dL_dy_pred = (2 / N) * (y_pred - y)
        dL_dW, dL_db, _ = linear_backward(dL_dy_pred, X, W)

        # Update
        sgd_step(W, b, dL_dW, dL_db, lr)

    print(f"Final W: {np.round(W.flatten(), 4)}")
    print(f"Final b: {np.round(b, 4)}")
