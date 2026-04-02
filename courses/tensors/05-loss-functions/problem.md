# Loss Functions and Their Gradients

## Your Task

Implement two fundamental loss functions and their analytic gradients with respect
to the predictions `y_pred`.

### Functions to implement

1. **`mse_loss(y_pred, y_true)`** — Mean Squared Error

$$\mathcal{L}_{\text{MSE}} = \frac{1}{N} \sum_{i=1}^{N} (y_{\text{pred},i} - y_{\text{true},i})^2$$

2. **`mse_grad(y_pred, y_true)`** — gradient of MSE w.r.t. `y_pred`

$$\frac{\partial \mathcal{L}_{\text{MSE}}}{\partial y_{\text{pred}}} = \frac{2}{N}(y_{\text{pred}} - y_{\text{true}})$$

3. **`bce_loss(y_pred, y_true)`** — Binary Cross-Entropy

$$\mathcal{L}_{\text{BCE}} = -\frac{1}{N} \sum_{i=1}^{N} \left[ y_{\text{true},i} \log y_{\text{pred},i} + (1 - y_{\text{true},i}) \log(1 - y_{\text{pred},i}) \right]$$

Clip `y_pred` to the range $[\varepsilon,\, 1-\varepsilon]$ (use $\varepsilon = 10^{-7}$) before
taking logs to avoid $\log(0)$.

4. **`bce_grad(y_pred, y_true)`** — gradient of BCE w.r.t. `y_pred`

$$\frac{\partial \mathcal{L}_{\text{BCE}}}{\partial y_{\text{pred}}} = -\frac{1}{N}\left(\frac{y_{\text{true}}}{y_{\text{pred}}} - \frac{1 - y_{\text{true}}}{1 - y_{\text{pred}}}\right)$$

Apply the same clipping to `y_pred` inside `bce_grad` as well.

### Constraints

- Use NumPy for array arithmetic.
- All functions take and return NumPy arrays.
- Losses must return a **scalar** (a single float).
- Gradients must return an **array of the same shape as `y_pred`**.

## Examples

```python
import numpy as np

y_pred = np.array([0.9, 0.2, 0.8, 0.4])
y_true = np.array([1.0, 0.0, 1.0, 0.0])

print(round(mse_loss(y_pred, y_true), 4))   # 0.0625
print(mse_grad(y_pred, y_true).round(4))    # [-0.05  0.1  -0.1   0.2 ]

print(round(bce_loss(y_pred, y_true), 4))   # 0.2656
print(bce_grad(y_pred, y_true).round(4))    # [-0.2778  0.3125 -0.3125  0.4167]
```

## What to print

Your `__main__` block should:

1. Define fixed test arrays `y_pred` and `y_true` (use the values above).
2. Print MSE loss and gradient, each rounded to 4 decimal places.
3. Print BCE loss and gradient, each rounded to 4 decimal places.
4. Run a **numerical gradient check** for both losses and print the max absolute
   error — it should be below `1e-5`.
