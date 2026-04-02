# Theory: Manual Gradients and Backpropagation

## The Computation Graph

For a linear regression model, the forward pass is a chain of simple operations:

```
X, W  →  matmul  →  Z  →  add b  →  y_pred  →  MSE  →  loss
```

To train the model, we need $\frac{\partial L}{\partial W}$ and
$\frac{\partial L}{\partial b}$ — the gradient of the loss with respect to
each learnable parameter. We compute these by working **backwards** through
the graph using the **chain rule**.

---

## The Chain Rule

If $L = f(g(x))$, then:

$$\frac{dL}{dx} = \frac{dL}{dg} \cdot \frac{dg}{dx}$$

For composed functions with intermediate variables — which is exactly what a
neural network is — we apply this rule at each step, passing gradients
backwards from the loss toward the parameters.

---

## Step 1 — Gradient of MSE Loss

The MSE loss is:

$$L = \frac{1}{N} \sum_{i=1}^{N} (\hat{y}_i - y_i)^2$$

Taking the derivative with respect to $\hat{y}_i$ (the prediction for sample $i$):

$$\frac{\partial L}{\partial \hat{y}_i} = \frac{2}{N} (\hat{y}_i - y_i)$$

In matrix form, for all $N$ samples at once:

$$\frac{\partial L}{\partial \hat{\mathbf{y}}} = \frac{2}{N} (\hat{\mathbf{y}} - \mathbf{y}) \quad \in \mathbb{R}^{N \times 1}$$

This is the **upstream gradient** passed into the linear layer's backward pass.

---

## Step 2 — Gradient Through the Linear Layer

The linear layer computes $\hat{\mathbf{y}} = XW + \mathbf{b}$, where
$X \in \mathbb{R}^{N \times D}$, $W \in \mathbb{R}^{D \times 1}$,
$\mathbf{b} \in \mathbb{R}^{1}$.

Let $\delta = \frac{\partial L}{\partial \hat{\mathbf{y}}} \in \mathbb{R}^{N \times 1}$
be the upstream gradient.

### Gradient with respect to W

We want $\frac{\partial L}{\partial W} \in \mathbb{R}^{D \times 1}$.

Expanding the loss in terms of $W$:

$$L = \frac{1}{N} \| XW + b - y \|^2$$

Differentiating, or equivalently applying the chain rule through the matmul:

$$\frac{\partial L}{\partial W} = X^\top \delta$$

**Intuition**: each row of $X$ (one input sample) contributed to one row of
$\hat{\mathbf{y}}$. To accumulate how much each feature $d$ in $W$ affected the
loss, we sum over all $N$ samples — which is exactly the matrix product $X^\top \delta$.

### Gradient with respect to b

The bias is broadcast across all $N$ samples:

$$\frac{\partial L}{\partial b} = \sum_{i=1}^{N} \delta_i = \mathbf{1}^\top \delta$$

In NumPy: `dL_dy_pred.sum()`.

### Gradient with respect to X

Although we do not update $X$ (it is data, not a parameter), this gradient is
essential when stacking layers — it becomes the upstream gradient for the layer
below:

$$\frac{\partial L}{\partial X} = \delta W^\top \quad \in \mathbb{R}^{N \times D}$$

---

## Step 3 — Gradient Descent Update

Gradient descent moves each parameter in the direction **opposite** to its gradient:

$$W \leftarrow W - \eta \frac{\partial L}{\partial W}$$

$$b \leftarrow b - \eta \frac{\partial L}{\partial b}$$

where $\eta > 0$ is the **learning rate**.

### Why the Negative Sign?

The gradient $\nabla_W L$ points in the direction of **steepest ascent** — the
direction that increases the loss most quickly. Subtracting it moves us toward
a local minimum of the loss surface.

### Choosing the Learning Rate

| $\eta$ | Effect |
|--------|--------|
| Too large | Loss diverges or oscillates |
| Too small | Convergence is very slow |
| Just right | Loss decreases smoothly and quickly |

For this problem, $\eta = 0.1$ works well. In practice, learning rate schedules
and adaptive optimisers (Adam, AdaGrad) handle this automatically.

---

## Connection to Backpropagation

What you have implemented **is** backpropagation — for a single-layer network.
In a deep network:

1. Run the **forward pass**, storing intermediate activations.
2. Compute the **loss**.
3. Run the **backward pass**: propagate $\frac{\partial L}{\partial \hat{y}}$
   backwards through each layer using the chain rule, accumulating gradients
   for every learnable parameter.
4. Apply **gradient descent** (or a more sophisticated optimiser) to update
   parameters.

Autograd engines (PyTorch, JAX) automate step 3 by recording the computation
graph during the forward pass and automatically differentiating it — but the
mathematics is identical to what you derived here.
