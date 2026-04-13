# Solution: Element-wise Operations and Activation Functions

## Key Insight

All three activations are just pointwise nonlinearities — each output element depends only on the corresponding input element. Their derivatives are equally simple and, crucially, can be expressed in terms of the activation's own output (not the input), which saves a forward-pass computation during backprop.

## ReLU

$$\text{ReLU}(x) = \max(0, x)$$

```python
def relu(x):
    return np.maximum(0, x)
```

**Derivative**: 1 where the gate was open, 0 where it was closed.

$$\frac{d}{dx}\text{ReLU}(x) = \begin{cases} 1 & x > 0 \\ 0 & x \leq 0 \end{cases}$$

```python
def relu_grad(x):
    return (x > 0).astype(float)
```

## Sigmoid

$$\sigma(x) = \frac{1}{1 + e^{-x}}$$

```python
def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))
```

**Derivative**: The elegant self-referential form — compute it once from the forward value:

$$\sigma'(x) = \sigma(x)\bigl(1 - \sigma(x)\bigr)$$

*Derivation*: Let $s = \sigma(x)$. Then $\frac{ds}{dx} = \frac{e^{-x}}{(1+e^{-x})^2} = s \cdot (1-s)$.

## Tanh

$$\tanh(x) = \frac{e^x - e^{-x}}{e^x + e^{-x}}$$

```python
def tanh(x):
    ex, emx = np.exp(x), np.exp(-x)
    return (ex - emx) / (ex + emx)
```

**Derivative**: Again expressible through the output:

$$\tanh'(x) = 1 - \tanh^2(x)$$

## Why These Derivatives Matter

During backpropagation, the gradient flows through an activation layer as:

$$\frac{\partial L}{\partial x} = \frac{\partial L}{\partial y} \cdot f'(x)$$

For ReLU, $f'(x) \in \{0, 1\}$ — it either lets gradients pass or kills them entirely. For sigmoid and tanh, the gradient is always in $[0, 0.25]$ and $[0, 1]$ respectively, which is why sigmoid networks suffer from vanishing gradients at saturation but tanh fares somewhat better.

## Gradient Check Pattern

Always verify analytic gradients with finite differences:

$$\nabla_x L \approx \frac{L(x + h) - L(x - h)}{2h}, \quad h = 10^{-5}$$

If the error is below $10^{-6}$, your derivative is correct.
