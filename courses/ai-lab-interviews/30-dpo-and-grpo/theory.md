# The DPO Loss

$$\mathcal{L}_{DPO} = -\mathbb{E}\left[\log\sigma\left(\beta\log\frac{\pi_\theta(y_w|x)}{\pi_{ref}(y_w|x)} - \beta\log\frac{\pi_\theta(y_l|x)}{\pi_{ref}(y_l|x)}\right)\right]$$

In code this is three lines, because log-probabilities turn the ratios into differences:

```python
chosen_reward   = beta * (policy_chosen_logps  - ref_chosen_logps)
rejected_reward = beta * (policy_rejected_logps - ref_rejected_logps)
loss = -F.logsigmoid(chosen_reward - rejected_reward).mean()
```

`F.logsigmoid` rather than `torch.log(torch.sigmoid(...))` — the fused version is numerically stable for large negative arguments, where the naive form takes the log of an underflowed zero. That is the module-18 lesson showing up in production code.

## The properties, and why each one is a test

**$\ln 2$ at initialization.** With $\pi_\theta = \pi_{ref}$, both implicit rewards are zero, their difference is zero, $\sigma(0) = 0.5$, and $-\log 0.5 = 0.6931$. Any DPO run whose loss does not start there has a bug — usually a reference model that is not actually the initial policy, or a mask mismatch between the two forward passes.

**Shift invariance.** Add any constant $c$ to both policy log-probabilities and the loss is unchanged, because only the difference of implicit rewards enters. This is the finite echo of the partition function cancelling: $Z(x)$ is a per-prompt constant, and constants do not survive a difference.

**Equal and opposite gradients.** Differentiating, the gradient with respect to the chosen log-probability is $-\beta\sigma(-\Delta)$ and with respect to the rejected one is $+\beta\sigma(-\Delta)$, for the same $\Delta$. They have identical magnitude.

That last property has a practical consequence worth stating in an interview: nothing in the objective anchors the *absolute* log-probabilities. The loss only cares about the gap, so both can drift downward together while the loss improves — and empirically they often do. That is the mechanism behind reports of DPO degrading a model in ways the training curve does not show, and it is why variants like IPO and ORPO exist.

## The prompt mask

`sequence_logprob` takes a mask because in a real implementation you sum only over **response** tokens.

Worth being precise about *why*, because the obvious reason is wrong: for DPO specifically, the prompt term is identical in the chosen and rejected branches and enters $\Delta$ with opposite signs, so it **cancels exactly** and the loss value is unaffected. Masking matters for three other reasons. It is mandatory in SFT, where there is no difference to cancel it. It becomes load-bearing the moment you length-normalize, a common DPO variant, since the prompt would then distort the divisor. And it keeps the policy and reference passes consistent, which is what makes the $\ln 2$ initialization check meaningful.

# The GRPO Loss

## Advantages

$$A_i = \frac{r_i - \mathrm{mean}(r_1..r_G)}{\mathrm{std}(r_1..r_G) + \epsilon}$$

The group's own statistics replace PPO's learned value network. With binary verifiable rewards this has a beautiful interpretation: the mean is the **pass rate** for that prompt, so a response's advantage is how it did relative to how hard the problem turned out to be.

**The degenerate case matters.** If all $G$ responses receive the same reward — the problem was trivial, or nobody solved it — the numerator is zero for every sample and the prompt contributes exactly nothing to the gradient. In a real run a large fraction of prompts can end up in this state, which is why GRPO training pipelines care about prompt difficulty curricula and about filtering prompts by observed pass rate.

**The std division is itself contested, and knowing that is current.** Dividing by the group's standard deviation amplifies the advantage on prompts whose groups barely disagree — the nearly-all-right and nearly-all-wrong ones — so the easiest and hardest questions get up-weighted relative to the informative middle. Later work (Dr. GRPO, 2025) drops the std division and keeps only the mean baseline for exactly this reason, and also fixes a length bias in how the original loss averages over tokens. "What is wrong with GRPO's advantage?" is a live follow-up, and this is the answer.

## The clipped surrogate

$$\mathcal{L} = -\mathbb{E}\left[\min\big(\rho_i A_i,\ \mathrm{clip}(\rho_i, 1-\epsilon, 1+\epsilon)A_i\big)\right] + \beta\,\mathrm{KL}$$

with $\rho_i = \exp(\log\pi_\theta - \log\pi_{old})$.

The `min` is what makes this a *pessimistic* bound. For a positive advantage it caps the gain at $1+\epsilon$, so a sample the policy now loves cannot pull it further.

The negative-advantage side is **asymmetric**, and this is a good follow-up to know: if the ratio *fell*, the penalty is capped at $1-\epsilon$; but if the ratio *rose* on a negative-advantage sample, $\min$ selects the unclipped term and the penalty is unbounded. At $A = -1$ and $\rho = 100$ the surrogate contributes $-100$. That is deliberate — it lets the update push hard away from an action that turned out badly — and it is exactly the gap Dual-Clip PPO closes with a second, lower bound.

Note the sign convention: the surrogate is something to *maximize*, so the returned loss negates it. Getting that backwards produces a run that confidently trains in the wrong direction, and it is a genuinely common bug.

## The KL estimator

GRPO uses the **k3** estimator rather than the naive log-ratio:

$$\mathrm{KL}_{k3} = \mathbb{E}\big[e^{r} - r - 1\big], \qquad r = \log\pi_{ref} - \log\pi_\theta$$

Why not just $\mathbb{E}[-r]$? Because that estimator, while unbiased, has high variance and can come out **negative** on a finite sample — and a negative KL penalty pushes the policy *away* from the reference, which is the opposite of the intent. The k3 form is unbiased and provably non-negative, since $e^r - r - 1 \ge 0$ for all real $r$ with equality only at $r = 0$.

The script checks exactly that: zero at equality, positive when the reference is above the policy, and positive when it is below.
