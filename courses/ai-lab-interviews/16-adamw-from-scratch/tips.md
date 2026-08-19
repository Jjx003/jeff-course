# Debugging Guide

**Parameters drift from torch by ~1e-3.** Look at the `eps` placement: it belongs added to `sqrt(v_hat)`, not to `v_hat` before the square root.

**Divergence grows over steps rather than appearing at once.** Bias correction. Check `t` increments before it is used and starts at 1.

**Everything matches `torch.optim.Adam` but not `AdamW`.** You folded the decay into the gradient. Move it to `p`.

**The clipping direction check fails.** You are computing a per-tensor norm rather than one global norm across all gradients.

**The learning rate rises again late in training.** `progress` is not clamped at 1, so the cosine wraps past $\pi$.

**In-place ops raise a autograd error.** Wrap `step` in `@torch.no_grad()`, and mutate `p` rather than `p.data` inside that context — that is what torch does.

# Rapid-Fire Answers

**"What is the first Adam step's size?"**
> Exactly the learning rate, whatever the gradient is, because bias correction makes `m_hat / sqrt(v_hat)` equal `g / |g|` at `t = 1`.

**"Why global rather than per-tensor gradient clipping?"**
> Global scaling preserves the update's direction and only bounds its magnitude. Per-tensor clipping scales tensors by different factors, which rotates the update into a different direction.

**"How much does decoupled decay actually change?"**
> Meaningfully. In this exercise, 25 steps at `lambda = 0.1` move the parameters apart by roughly 0.48. The coupled version passes decay through the `sqrt(v)` normalization, so parameters with large gradients get decayed less — the regularization strength ends up depending on gradient magnitude.

**"Which parameters should not get weight decay?"**
> Biases and normalization gains. Decaying a norm's scale toward zero shrinks the activations it exists to normalize. Handle it with parameter groups.

# Variations to Expect

- **"Now add AMSGrad."** Keep a running max of `v` and use that in the denominator, so the effective step size never increases.
- **"Now implement Lion."** Sign-based: `update = sign(beta1 * m + (1 - beta1) * g)`, with `m` updated using `beta2`. One state tensor instead of two, so half the optimizer memory.
- **"What about Muon?"** Momentum SGD on each 2-D weight matrix, with the update orthogonalized by a few Newton-Schulz iterations before it is applied; embeddings, the head, and norms stay on AdamW. One momentum buffer, and validated at frontier scale (Kimi K2). Know the one-line why: it equalizes the update across matrix directions the way Adam equalizes across coordinates.
- **"Make it memory-efficient."** 8-bit moments with block-wise quantization, or factored second moments as in Adafactor.
- **"Add gradient accumulation."** Divide the loss by the accumulation count, step every `k` micro-batches, and note that clipping must happen after the last accumulation, not per micro-batch.

# Further Reading

- [Adam](https://arxiv.org/abs/1412.6980) and [AdamW](https://arxiv.org/abs/1711.05101)
- [torch's AdamW source](https://github.com/pytorch/pytorch/blob/main/torch/optim/adamw.py) — worth reading once for the parameter-group and state-handling patterns.
- [Symbolic Discovery of Optimization Algorithms](https://arxiv.org/abs/2302.06675) — Lion, and a good example of the "what else could an optimizer be" question.
