# Element-wise Operations and Activation Functions

## Your Task

Now that you have tensors, matrix multiplication, and broadcasting under your belt,
it's time to implement the building blocks of neural network nonlinearity: **activation functions**.

Unlike the previous problems, **NumPy is allowed here**. Your goal is to implement each
function correctly using NumPy primitives and understand the derivative formulas that
you'll need for backpropagation.

### Functions to Implement

1. **`relu(x: np.ndarray) -> np.ndarray`**
   The Rectified Linear Unit. Passes positive values through, zeros out negatives:

   $$\text{ReLU}(x) = \max(0, x)$$

2. **`sigmoid(x: np.ndarray) -> np.ndarray`**
   Maps any real number to $(0, 1)$:

   $$\sigma(x) = \frac{1}{1 + e^{-x}}$$

3. **`tanh(x: np.ndarray) -> np.ndarray`**
   Maps any real number to $(-1, 1)$:

   $$\tanh(x) = \frac{e^x - e^{-x}}{e^x + e^{-x}}$$

   Implement this using the exponential formula directly (you may use `np.exp`).

4. **`relu_grad(x: np.ndarray) -> np.ndarray`**
   Derivative of ReLU with respect to $x$:

   $$\frac{d}{dx}\text{ReLU}(x) = \begin{cases} 1 & x > 0 \\ 0 & x \leq 0 \end{cases}$$

5. **`sigmoid_grad(x: np.ndarray) -> np.ndarray`**
   Derivative of sigmoid — elegantly expressed in terms of $\sigma$ itself:

   $$\frac{d\sigma}{dx} = \sigma(x)\,(1 - \sigma(x))$$

6. **`tanh_grad(x: np.ndarray) -> np.ndarray`**
   Derivative of tanh — similarly self-referential:

   $$\frac{d\tanh}{dx} = 1 - \tanh(x)^2$$

### Requirements

- All functions accept and return `np.ndarray`.
- Your implementations must be **vectorized** (no Python loops over elements).
- `tanh` must be implemented using the exponential formula, not by calling `np.tanh` directly.

## Examples

```python
import numpy as np

x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])

print(relu(x))
# [0. 0. 0. 1. 2.]

print(sigmoid(x))
# [0.1192 0.2689 0.5    0.7311 0.8808]

print(tanh(x))
# [-0.9640 -0.7616  0.0000  0.7616  0.9640]

print(relu_grad(x))
# [0. 0. 0. 1. 1.]

print(sigmoid_grad(x))
# [0.1050 0.1966 0.2500 0.1966 0.1050]

print(tanh_grad(x))
# [0.0707 0.4200 1.0000 0.4200 0.0707]
```

## Numerical Gradient Check

A good sanity check for any derivative is the **central difference** formula:

$$f'(x) \approx \frac{f(x + h) - f(x - h)}{2h}, \quad h = 10^{-5}$$

Your main block verifies that `sigmoid_grad` matches this numerical estimate within
a tolerance of $10^{-6}$.
