# Solution: Manual Gradients — Linear Regression

## Key Ideas

### Forward pass

The prediction is a single matrix multiply plus broadcast bias:

```python
y_pred = X @ W + b   # shape (N, 1)
```

### MSE loss

A one-liner using NumPy:

```python
np.mean((y_pred - y) ** 2)
```

### Backward pass

Apply the chain rule mechanically through each operation:

- `dL_dy_pred = (2 / N) * (y_pred - y)` — gradient of MSE w.r.t. the prediction
- `dL_dW = X.T @ dL_dy_pred` — how loss changes as each weight changes
- `dL_db = dL_dy_pred.sum()` — bias gradient is just the sum (bias is broadcast across all N rows)
- `dL_dX = dL_dy_pred @ W.T` — needed if inputs also have gradients

The upstream gradient `dL_dy_pred` must already include the `2/N` factor from
MSE before it is passed to `linear_backward`.

### SGD update

In-place subtraction keeps parameters as the same NumPy array objects:

```python
W -= lr * dL_dW
b -= lr * dL_db
```

## Common Mistakes

- **Transposing the wrong matrix**: `dL_dW = X.T @ dL_dy_pred`, not `dL_dy_pred.T @ X`.
- **Missing the `2/N` factor**: the `mse_loss` function returns the mean of squared
  residuals; its gradient must include both the factor of 2 from the square and
  `1/N` from the mean. If you compute the upstream gradient inside `linear_backward`
  you will get a shape mismatch or wrong scale.
- **Scalar vs array bias**: `b` has shape `(1,)` so `dL_db = dL_dy_pred.sum()` is a
  scalar float, but the in-place update `b -= lr * dL_db` still works because NumPy
  broadcasts.
- **Re-using the seed**: the dataset and the initial parameters both use
  `np.random.seed(42)`. Reset the seed a second time before initialising `W` and `b`
  or the parameter values will differ.
