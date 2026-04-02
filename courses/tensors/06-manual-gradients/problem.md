# Manual Gradients: Linear Regression

## Your Task

Before building autograd, you will manually derive and implement gradients for
a single linear layer trained with MSE loss. This is backpropagation for a
1-layer network — done entirely by hand.

### Setup

Given:

- Input `X`: shape `(N, D)` — N samples, D features
- Weights `W`: shape `(D, 1)`
- Bias `b`: shape `(1,)`
- Targets `y`: shape `(N, 1)`

### Requirements

1. **`linear_forward(X, W, b)`**
   Compute the prediction `y_pred = X @ W + b`. Return `y_pred` with shape `(N, 1)`.

2. **`mse_loss(y_pred, y)`**
   Compute the mean squared error: $\frac{1}{N} \sum_{i=1}^{N} (\hat{y}_i - y_i)^2$.
   Return a scalar.

3. **`linear_backward(dL_dy_pred, X, W)`**
   Given the upstream gradient `dL_dy_pred` (shape `(N, 1)`), return a tuple
   `(dL_dW, dL_db, dL_dX)`:
   - `dL_dW = X.T @ dL_dy_pred` — shape `(D, 1)`
   - `dL_db = dL_dy_pred.sum()` — scalar
   - `dL_dX = dL_dy_pred @ W.T` — shape `(N, D)`

4. **`sgd_step(W, b, dL_dW, dL_db, lr)`**
   Apply one step of gradient descent in-place:
   - `W -= lr * dL_dW`
   - `b -= lr * dL_db`

5. **Training loop**: assemble the above functions into a loop that runs for
   100 steps on a toy dataset.

### What to Print

After training, print (each value rounded to 4 decimal places):

```
Step   0 | loss: <initial loss>
Step  50 | loss: <loss at step 50>
Step  99 | loss: <final loss>
Final W: <W values>
Final b: <b value>
```

### Toy Dataset

Generate the dataset as follows (use `np.random.seed(42)` before everything):

```python
np.random.seed(42)
N, D = 50, 2
X = np.random.randn(N, D)
true_W = np.array([[2.0], [-1.0]])
true_b = np.array([0.5])
noise = 0.1 * np.random.randn(N, 1)
y = X @ true_W + true_b + noise
```

Then reset the seed and initialise parameters:

```python
np.random.seed(42)
W = np.random.randn(D, 1)
b = np.zeros(1)
```

Use a learning rate of `0.1` and train for 100 steps.

## Examples

```python
# Forward pass
y_pred = linear_forward(X, W, b)    # shape (N, 1)
loss   = mse_loss(y_pred, y)        # scalar

# Backward pass — compute upstream gradient first
dL_dy_pred = (2 / N) * (y_pred - y)   # shape (N, 1)
dL_dW, dL_db, dL_dX = linear_backward(dL_dy_pred, X, W)

# Update
sgd_step(W, b, dL_dW, dL_db, lr=0.1)
```
