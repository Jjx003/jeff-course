# The Step, Line by Line

```python
state["t"] += 1
t = state["t"]

m.mul_(beta1).add_(g, alpha=1 - beta1)
v.mul_(beta2).addcmul_(g, g, value=1 - beta2)

m_hat = m / (1 - beta1 ** t)
v_hat = v / (1 - beta2 ** t)

p.add_(p, alpha=-lr * weight_decay)
p.addcdiv_(m_hat, v_hat.sqrt().add_(eps), value=-lr)
```

**`t` starts at 1.** At $t=0$ the bias correction divides by $1 - \beta^0 = 0$.

**`v` accumulates the element-wise square**, not the squared norm. `addcmul_(g, g, ...)` rather than anything involving a dot product.

**The decay touches `p`, not `g`.** That single line is the entire difference between Adam and AdamW, and the script measures how much it matters — with $\lambda = 0.1$ over 25 steps, the parameters diverge by about 0.48, which is enormous for a model that started near zero.

**`eps` goes inside**, added to $\sqrt{\hat{v}}$ rather than to $\hat{v}$. Both prevent division by zero; only the first matches torch, and it also behaves better for genuinely tiny second moments.

## The step-one identity

A property worth knowing because it makes an elegant test:

$$\hat{m}_1 = \frac{(1-\beta_1)g}{1-\beta_1} = g, \qquad \hat{v}_1 = \frac{(1-\beta_2)g^2}{1-\beta_2} = g^2$$

so the update is $\eta \cdot g/|g| = \eta$ exactly, regardless of the gradient's magnitude. Adam's first step always has size $\eta$.

Without bias correction it would be

$$\eta\frac{(1-\beta_1)g}{\sqrt{(1-\beta_2)g^2}} = \eta\frac{1-\beta_1}{\sqrt{1-\beta_2}}$$

which at $\beta_1=0.9, \beta_2=0.95$ is $0.447\eta$ — under-stepping early, in exactly the direction that makes the *later* steps oversized as $v$ catches up.

## The schedule

```python
if step < warmup:
    return peak * step / warmup
progress = (step - warmup) / (total - warmup)
return peak * (min_frac + (1 - min_frac) * 0.5 * (1 + cos(pi * progress)))
```

Three details to get right:

- Clamp `progress` at 1, or a run that goes past `total` produces a rising learning rate as the cosine comes back up. That has happened in production.
- The floor is a *fraction of peak*, not an absolute value — the convention everywhere.
- Warmup uses `step / warmup`, so step 0 gives exactly 0 and step `warmup` gives exactly the peak.

## Global versus per-tensor clipping

```python
total = sqrt(sum((g ** 2).sum() for g in grads))
if total > max_norm:
    for g in grads:
        g.mul_(max_norm / (total + 1e-6))
```

Every gradient is scaled by the *same* factor, computed from the norm across all of them. So the update direction in parameter space is unchanged and only its magnitude is bounded.

Clipping each tensor against its own threshold would scale different tensors by different factors, **rotating** the update. That is a different algorithm with different behavior, and the distinction is a standard follow-up question. The script checks it by measuring the cosine similarity of each gradient before and after clipping — all exactly 1.

The `+1e-6` guards against dividing by zero and is what torch does; it also means the post-clip norm is a hair under the threshold rather than exactly on it.
