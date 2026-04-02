# Theory: Loss Functions and Their Gradients

## The Training Objective

Training a neural network means finding parameters $\theta$ that minimise a **loss
function** $\mathcal{L}(\theta)$ measuring how wrong the model's predictions are.
Gradient descent updates parameters by stepping in the direction that reduces the
loss:

$$\theta \leftarrow \theta - \eta \, \nabla_\theta \mathcal{L}$$

To propagate this gradient through a network (backpropagation), we first need
$\frac{\partial \mathcal{L}}{\partial \hat{y}}$ — the gradient of the loss with
respect to the output predictions. That is exactly what this problem asks you to
implement.

---

## Mean Squared Error (MSE)

### Definition

$$\mathcal{L}_{\text{MSE}} = \frac{1}{N} \sum_{i=1}^{N} (\hat{y}_i - y_i)^2$$

$N$ is the number of samples, $\hat{y}$ are predictions, $y$ are targets.

### When to use it

MSE is the standard loss for **regression** tasks (predicting a continuous value).
It follows from assuming the prediction errors are drawn from a Gaussian distribution
and maximising the log-likelihood of the data under that assumption.

### Gradient

Differentiating with respect to $\hat{y}_i$:

$$\frac{\partial \mathcal{L}_{\text{MSE}}}{\partial \hat{y}_i} = \frac{2}{N}(\hat{y}_i - y_i)$$

In vector form: $\nabla_{\hat{y}} \mathcal{L}_{\text{MSE}} = \frac{2}{N}(\hat{y} - y)$.

The gradient is **proportional to the residual** — large errors produce large
gradients, naturally emphasising outliers. This is both MSE's strength (fast
correction of big errors) and weakness (sensitivity to outliers).

---

## Binary Cross-Entropy (BCE)

### Definition

$$\mathcal{L}_{\text{BCE}} = -\frac{1}{N} \sum_{i=1}^{N} \left[ y_i \log \hat{y}_i + (1 - y_i) \log(1 - \hat{y}_i) \right]$$

where $y_i \in \{0, 1\}$ and $\hat{y}_i \in (0, 1)$.

### Information-theoretic view

BCE is the **cross-entropy** between the true distribution $p = y_i$ and the
predicted distribution $q = \hat{y}_i$ for a Bernoulli random variable:

$$H(p, q) = -p \log q - (1-p) \log(1-q)$$

Minimising BCE is equivalent to maximising the log-likelihood of the data under
a Bernoulli model — the standard objective for binary classification.

### Why not MSE for classification?

MSE produces a non-convex loss surface for sigmoid outputs, leading to slow and
unreliable training. BCE is convex in the logit space and its gradient vanishes
correctly only when the prediction is perfect.

### Numerical stability

$\log(0)$ is $-\infty$. In practice, predictions are clipped:

$$\hat{y}_i^{\text{safe}} = \text{clip}(\hat{y}_i, \varepsilon, 1 - \varepsilon), \quad \varepsilon = 10^{-7}$$

### Gradient

$$\frac{\partial \mathcal{L}_{\text{BCE}}}{\partial \hat{y}_i} = -\frac{1}{N}\left(\frac{y_i}{\hat{y}_i} - \frac{1 - y_i}{1 - \hat{y}_i}\right)$$

When $y_i = 1$ this simplifies to $-\frac{1}{N\hat{y}_i}$; when $y_i = 0$ it
becomes $\frac{1}{N(1 - \hat{y}_i)}$.

---

## Numerical Gradient Checking

Before trusting an analytic gradient, verify it numerically using the
**central-difference** formula:

$$\frac{\partial \mathcal{L}}{\partial \hat{y}_i} \approx \frac{\mathcal{L}(\hat{y} + \varepsilon \mathbf{e}_i) - \mathcal{L}(\hat{y} - \varepsilon \mathbf{e}_i)}{2\varepsilon}$$

where $\mathbf{e}_i$ is the $i$-th standard basis vector and $\varepsilon \approx 10^{-5}$.

If the maximum absolute difference between the numerical and analytic gradients
is below $10^{-5}$, your implementation is almost certainly correct. This check
is indispensable during the development of a new layer or loss function.
