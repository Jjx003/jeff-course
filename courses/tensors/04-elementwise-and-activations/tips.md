# Tips & Notes

## ReLU in One Line

NumPy's `np.maximum` broadcasts element-wise against a scalar:

```python
def relu(x):
    return np.maximum(0, x)
```

`np.maximum(a, b)` is not the same as `np.max(a)` — the former is element-wise,
the latter reduces to a single scalar.

## Sigmoid Numerically

The straightforward formula $1 / (1 + \exp(-x))$ is fine for this exercise.
In production you'd use `scipy.special.expit` or `torch.sigmoid` which handle
numerical edge cases (very large negative $x$ underflowing `exp`).

## Implementing Tanh Manually

Use the definition directly with `np.exp`:

```python
def tanh(x):
    ex  = np.exp(x)
    emx = np.exp(-x)
    return (ex - emx) / (ex + emx)
```

You can verify against `np.tanh(x)` — they should match to machine precision.

## Gradient of ReLU: Avoid `>=`

The derivative of ReLU is technically undefined at $x = 0$.
The convention used in all major frameworks is to set it to 0 at exactly 0:

```python
def relu_grad(x):
    return (x > 0).astype(float)
```

`(x > 0)` produces a boolean array; `.astype(float)` converts `True → 1.0`, `False → 0.0`.

## Numerical Gradient Check

```python
def numerical_grad(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)
```

Compare with your analytic gradient using `np.allclose(analytic, numeric, atol=1e-6)`.
If they disagree, double-check your formula — a common mistake is forgetting the chain
rule factor when the derivative is expressed in terms of the activation output.

## Printing Rounded Arrays

Use `np.round(arr, 4)` to produce deterministic output:

```python
print(np.round(relu(x), 4))
```

## Common Pitfalls

- **`np.exp` overflow**: for very large positive `x`, `np.exp(x)` returns `inf`.
  For this exercise the test inputs are small, so it's not a concern.
- **Wrong gradient formula**: sigmoid's derivative is $\sigma(x)(1-\sigma(x))$,
  which depends on the *sigmoid value*, not $x$ directly. Compute `s = sigmoid(x)` first.
- **Shape mismatch**: all these functions are element-wise, so the output shape
  is always identical to the input shape.
