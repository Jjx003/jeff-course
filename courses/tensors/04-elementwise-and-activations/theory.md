# Theory: Activation Functions

## Why Activations?

A neural network without activation functions is just a stack of matrix multiplications.
No matter how many layers you add, the composition of linear functions is still linear —
it collapses to a single affine transformation and cannot learn non-trivial patterns.

**Activation functions introduce nonlinearity** between layers. With nonlinear activations,
a deep network can approximate any continuous function (universal approximation theorem).

---

## ReLU — Rectified Linear Unit

$$\text{ReLU}(x) = \max(0, x)$$

ReLU is the most widely used activation in modern deep learning. Its appeal:

- **No vanishing gradient for positive inputs**: the gradient is exactly 1 for $x > 0$,
  so error signals flow back through deep networks without shrinking.
- **Computationally cheap**: just a comparison and a max — no expensive `exp` calls.
- **Sparse activations**: roughly half the neurons output 0, which can regularise the network.

### Derivative

$$\frac{d}{dx}\text{ReLU}(x) = \begin{cases} 1 & x > 0 \\ 0 & x \leq 0 \end{cases}$$

### Dead ReLU Problem

If a neuron's pre-activation is always negative (e.g., due to a large negative bias or a
bad weight update), its gradient is always 0 — it never learns again. This is called a
**dead ReLU**. Mitigations include Leaky ReLU ($\alpha x$ for $x < 0$, small $\alpha > 0$)
and careful weight initialisation.

---

## Sigmoid

$$\sigma(x) = \frac{1}{1 + e^{-x}}$$

Sigmoid squashes inputs to the range $(0, 1)$, making it natural for **binary classification
outputs** (interpreting the output as a probability).

### Derivative

$$\sigma'(x) = \sigma(x)\,(1 - \sigma(x))$$

This is derived by applying the quotient rule and noticing a beautiful self-referential
structure. For a network output $\hat{y} = \sigma(z)$, the gradient with respect to $z$
is just $\hat{y}(1 - \hat{y})$.

### Vanishing Gradient Problem

For large $|x|$, sigmoid **saturates**: $\sigma(x) \approx 0$ or $\sigma(x) \approx 1$.
In these regions $\sigma'(x) \approx 0$, so gradients vanish as they propagate backwards
through saturated neurons. This is why sigmoid is **not recommended as a hidden-layer
activation** in deep networks — use ReLU instead. It remains common at the output layer
for binary problems.

---

## Tanh

$$\tanh(x) = \frac{e^x - e^{-x}}{e^x + e^{-x}}$$

Tanh is a **zero-centred** version of sigmoid, mapping inputs to $(-1, 1)$.
Zero-centred outputs make the next layer's weight updates less correlated, which can
speed up convergence compared to sigmoid.

The relationship between the two is:

$$\tanh(x) = 2\sigma(2x) - 1$$

### Derivative

$$\tanh'(x) = 1 - \tanh(x)^2$$

Like sigmoid, tanh saturates for large $|x|$, though its stronger gradient near 0
(peak value 1 vs 0.25 for sigmoid) makes it somewhat less prone to vanishing gradients.

---

## Derivatives at a Glance

| Activation | Formula | Derivative | Max gradient |
|------------|---------|------------|--------------|
| ReLU | $\max(0,x)$ | $\mathbf{1}[x>0]$ | 1 |
| Sigmoid | $\frac{1}{1+e^{-x}}$ | $\sigma(1-\sigma)$ | 0.25 |
| Tanh | $\frac{e^x-e^{-x}}{e^x+e^{-x}}$ | $1-\tanh^2$ | 1 |

---

## Numerical Gradient Checking

When implementing derivatives by hand it's easy to make a sign error or miss a factor.
The **central difference** approximation gives an independent estimate:

$$f'(x) \approx \frac{f(x + h) - f(x - h)}{2h}$$

For $h = 10^{-5}$ this typically agrees with the analytic gradient to 6 significant figures.
This technique is standard practice when debugging backpropagation.
