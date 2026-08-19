# The Four Gradients

With $X \in \mathbb{R}^{N \times D}$, $W_1 \in \mathbb{R}^{D \times H}$, $W_2 \in \mathbb{R}^{H \times C}$:

$$Z_1 = XW_1 + b_1, \qquad H_1 = \mathrm{ReLU}(Z_1), \qquad Z_2 = H_1W_2 + b_2$$

$$L = \frac{1}{N}\sum_{i=1}^{N} -\log \mathrm{softmax}(Z_2)_{i, t_i}$$

Working backward:

$$\frac{\partial L}{\partial Z_2} = \frac{P - \mathrm{onehot}(t)}{N} \in \mathbb{R}^{N \times C}$$

$$\frac{\partial L}{\partial W_2} = H_1^{\top}\frac{\partial L}{\partial Z_2}, \qquad \frac{\partial L}{\partial b_2} = \sum_{i}\frac{\partial L}{\partial Z_{2,i,:}}$$

$$\frac{\partial L}{\partial H_1} = \frac{\partial L}{\partial Z_2}W_2^{\top}, \qquad \frac{\partial L}{\partial Z_1} = \frac{\partial L}{\partial H_1}\odot \mathbb{1}[Z_1 > 0]$$

$$\frac{\partial L}{\partial W_1} = X^{\top}\frac{\partial L}{\partial Z_1}, \qquad \frac{\partial L}{\partial b_1} = \sum_{i}\frac{\partial L}{\partial Z_{1,i,:}}$$

Every one of these is forced by Rule 1 (gradient shape equals tensor shape) plus Rule 2 (shared tensors contract the batch, unshared ones keep it). If you can recite those two rules, you can rebuild this table live.

## Where the `1/N` goes

The mean reduction contributes a factor of $1/N$ that has to appear exactly once. The cleanest convention, and the one the starter uses, is to fold it into `dlogits` and never think about it again. Applying it twice gives gradients that are a factor of $N$ too small — the model still trains, just $N$ times slower, which is a genuinely nasty bug to find in the wild and an excellent thing to have already made a mistake about in practice.

## Numerically stable softmax

Never exponentiate raw logits. Subtract the row max first:

$$\mathrm{softmax}(x)_i = \frac{e^{x_i - x_{\max}}}{\sum_j e^{x_j - x_{\max}}}$$

Softmax is invariant to a constant shift, so this changes nothing mathematically. It changes everything numerically: in float32, $e^{x}$ overflows around $x \approx 88$. After subtracting the max, the largest exponent is $e^0 = 1$ and the denominator is at least 1, so no overflow and no $\log(0)$.

For the loss itself, prefer the log-sum-exp form rather than taking a log of a probability:

$$\log \mathrm{softmax}(x)_i = x_i - \log\sum_j e^{x_j}$$

This avoids materializing tiny probabilities and then logging them.

## Why check gradients twice

Finite differences and autograd fail in different ways, which is precisely why both are worth running.

**Finite differences** catch genuine mathematical errors — a missing transpose, a dropped ReLU mask, the `1/N` in the wrong place. They are slow ($O(P)$ forward passes for $P$ parameters), noisy in float32, and useless for testing anything non-differentiable. Use float64 and a small model.

**Autograd comparison** catches convention errors: a different weight layout, a different reduction, a different definition of the loss. It cannot catch an error you made identically in both implementations, which is why it is a complement to finite differences and not a replacement.

The right answer to "how do you know your backward is right?" names both, and says why.
