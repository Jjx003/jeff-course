# Tips & Notes

## Clipping in BCE

Always clip before any `np.log` call — including inside `bce_grad`:

```python
eps = 1e-7
y_pred_safe = np.clip(y_pred, eps, 1 - eps)
```

Forgetting to clip in the gradient function is a common mistake that causes
`nan` or `inf` values to silently propagate through training.

## Scalar vs. array return

`np.mean(...)` already returns a scalar, so your loss functions are fine.
If you ever see shape mismatches downstream, check that you are not accidentally
returning an array from a loss.

## Numerical gradient check

Use the central-difference formula with $\varepsilon = 10^{-5}$:

```python
def numerical_grad(loss_fn, y_pred, y_true, eps=1e-5):
    grad = np.zeros_like(y_pred)
    for i in range(len(y_pred)):
        yp = y_pred.copy(); yp[i] += eps
        ym = y_pred.copy(); ym[i] -= eps
        grad[i] = (loss_fn(yp, y_true) - loss_fn(ym, y_true)) / (2 * eps)
    return grad
```

Compare with your analytic gradient:

```python
err = np.max(np.abs(numerical_grad(mse_loss, y_pred, y_true) - mse_grad(y_pred, y_true)))
print(f"MSE grad check error: {err:.2e}")   # should be < 1e-5
```

## Connecting to backprop

The gradient you return here flows **backward** into the network. In the next
problem (Manual Gradients) you will chain this loss gradient through each layer
using the chain rule — so make sure your gradient shapes are correct now.

## Edge cases worth testing

- All predictions correct (loss should be ≈ 0)
- All predictions wrong (loss should be large)
- Predictions very close to 0 or 1 in BCE (clipping matters here)
