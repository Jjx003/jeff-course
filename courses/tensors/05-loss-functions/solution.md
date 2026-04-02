# Solution: Loss Functions and Their Gradients

## Key Ideas

### MSE

The formula is a simple average of squared residuals. NumPy makes this a one-liner:

```python
np.mean((y_pred - y_true) ** 2)
```

The gradient follows directly from the chain rule on the squared term:
$\frac{d}{d\hat{y}_i}(\hat{y}_i - y_i)^2 = 2(\hat{y}_i - y_i)$, then divide by $N$.

### BCE

The only subtlety is numerical stability. Clip before every `np.log` call and
before every division:

```python
eps = 1e-7
y_pred_safe = np.clip(y_pred, eps, 1.0 - eps)
```

The loss and gradient are then straightforward translations of the mathematical
formulas into NumPy.

### Gradient check

The central-difference check confirms correctness: errors below $10^{-5}$ are
expected for well-implemented analytic gradients. Errors above $10^{-3}$ indicate
a sign error or a missing factor.

## Common Mistakes

- **Wrong sign in BCE gradient**: the minus sign at the front is easy to drop.
- **Forgetting the $1/N$ factor**: the gradient must match the loss scale.
- **Not clipping in the gradient**: causes `nan` when `y_pred` is exactly 0 or 1.
- **Returning an array from a loss**: loss functions must return a scalar for the
  gradient check to work correctly.
