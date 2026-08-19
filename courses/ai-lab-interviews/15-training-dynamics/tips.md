# AdamW From Memory

```python
for group in self.param_groups:
    lr, (b1, b2), eps, wd = group["lr"], group["betas"], group["eps"], group["weight_decay"]
    for p in group["params"]:
        if p.grad is None:
            continue
        state = self.state[p]
        t = state.get("t", 0) + 1
        m = state.get("m", torch.zeros_like(p))
        v = state.get("v", torch.zeros_like(p))

        g = p.grad
        m = b1 * m + (1 - b1) * g
        v = b2 * v + (1 - b2) * g * g
        m_hat = m / (1 - b1 ** t)
        v_hat = v / (1 - b2 ** t)

        p.data.add_(p.data, alpha=-lr * wd)             # decoupled decay
        p.data.addcdiv_(m_hat, v_hat.sqrt() + eps, value=-lr)

        state["t"], state["m"], state["v"] = t, m, v
```

Rehearse this until it is automatic. Then check yourself on three things people get wrong under pressure: `t` starts at **1**, the decay is applied to `p.data` and not to `g`, and `v` accumulates the **element-wise square**.

# Rapid-Fire Answers

**"Why bias correction?"**
> `m` and `v` start at zero, so early estimates are biased toward zero — at step 1 with `beta2 = 0.999`, `v` is 1000x too small while `m` is only 10x too small, leaving a first step about 3.2x too large. Dividing by `1 - beta^t` corrects it, and the correction fades as `beta^t` goes to zero.

**"Why warmup?"**
> Bias correction fixes the expected magnitude but not the variance: early `v` is estimated from a handful of samples and is noisy, so some parameters get enormous updates. Warmup keeps steps small until the estimates settle. It also stops the first few batches from dominating the model's early direction.

**"Adam versus AdamW?"**
> Adam adds `lambda * theta` to the gradient, so the decay passes through the `sqrt(v)` normalization and parameters with large gradients get decayed less. AdamW applies the decay directly to the parameter, decoupled from the adaptive scaling.

**"Why warmup-stable-decay over cosine?"**
> Cosine requires committing to a total step count up front. WSD holds at peak and only anneals at the end, so you can branch a checkpoint from the stable phase at any point and finish it. It buys experimental flexibility, not a better loss curve.

**"Loss spiked at step 40k. What do you do?"**
> Look at the gradient-norm trace first — a spike before the loss spike says it was the update, no spike says the forward pass. Then inspect the batch: corrupted data and pathological repetition are the usual causes. Mitigations are clipping, QK-norm, skipping high-norm batches, and rolling back to a checkpoint past the bad data.

**"How do you pick a learning rate for a model 10x larger?"**
> Either scale down from a known good value by roughly `1/sqrt(width ratio)`, or use μP, which parameterizes initialization and learning rates so the optimum is width-invariant and transfers from a small proxy model.

# Traps

- **Saying Adam and AdamW differ only in "where you put the decay"** without saying *why* it matters — that the coupling makes decay strength depend on gradient magnitude.
- **Applying weight decay to norms and biases.** Convention is matrices only.
- **Forgetting `t` starts at 1.** At `t=0` the bias correction divides by zero.
- **Claiming linear LR scaling with batch size for Adam.** Square-root is the better rule; the second moment already normalizes magnitude.
- **Not knowing the optimizer state is half of training memory.** 8 of the 16 bytes per parameter.

# Further Reading

- [Adam: A Method for Stochastic Optimization](https://arxiv.org/abs/1412.6980)
- [Decoupled Weight Decay Regularization](https://arxiv.org/abs/1711.05101) — the AdamW paper.
- [Tensor Programs V: Tuning Large Neural Networks via Zero-Shot Hyperparameter Transfer](https://arxiv.org/abs/2203.03466) — μP.
- [MiniCPM](https://arxiv.org/abs/2404.06395) — a clear account of warmup-stable-decay and why it was adopted.
- [Muon](https://kellerjordan.github.io/posts/muon/) — the original write-up of the orthogonalized-momentum optimizer.
- [PaLM](https://arxiv.org/abs/2204.02311) — section 5.1 on loss spikes is the canonical description of that failure mode.
