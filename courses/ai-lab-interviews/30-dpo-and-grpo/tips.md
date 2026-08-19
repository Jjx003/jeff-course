# Debugging Guide

**DPO loss does not start at 0.6931.** The reference log-probabilities are not the initial policy's. Check that the reference model is a frozen copy of the SFT checkpoint, and that the same mask is applied in both forward passes.

**DPO loss goes negative.** Impossible for `-logsigmoid` — you have a sign error, or you wrote `logsigmoid(rejected - chosen)`.

**DPO loss is `nan` or `inf`.** You used `log(sigmoid(x))` instead of `F.logsigmoid(x)`. For a large negative argument the sigmoid underflows to zero and the log diverges.

**GRPO advantages are all zero.** Either the group has uniform rewards, which is a real and expected condition, or you normalized across the wrong axis. Normalize within each prompt's group, not across the whole batch.

**GRPO loss has the wrong sign.** The surrogate is maximized; the loss is its negation. If the reward goes down as training proceeds, check this first.

**KL comes out negative.** You used the naive log-ratio estimator. Use `exp(r) - r - 1`.

# Rapid-Fire Answers

**"What should the DPO loss be at step 0?"**
> Exactly `ln 2 = 0.6931`. The policy equals the reference, so both implicit rewards are zero and the model is exactly indifferent between chosen and rejected. It is the fastest possible sanity check on a DPO setup.

**"What is DPO's implicit reward?"**
> `beta * log(policy / reference)`, which is what inverting the closed-form KL-regularized optimum gives you. The partition function drops out because only reward differences appear in the Bradley-Terry loss.

**"Why do people say DPO drags log-probs down?"**
> The gradients on chosen and rejected are equal and opposite, and nothing in the objective anchors absolute log-probabilities — only the gap. So both can drift downward while the loss improves, which degrades the model in ways the training curve does not show.

**"What replaces the value network in GRPO?"**
> The group's own reward statistics. Sample G responses per prompt, normalize rewards within the group, and use that as the advantage. With binary verifiable rewards the group mean is the pass rate, so an advantage is how a response did relative to the problem's difficulty.

**"What happens when a GRPO group has uniform rewards?"**
> Zero advantage, so zero gradient — the prompt is wasted. In practice a large fraction of prompts can land there, which is why difficulty curricula and pass-rate filtering matter.

**"Why the k3 KL estimator?"**
> The naive log-ratio estimator is unbiased but high-variance and can come out negative on a finite sample, which would push the policy away from the reference. `exp(r) - r - 1` is unbiased and provably non-negative.

# Variations to Expect

- **"Now add the reference-free variant."** ORPO folds an odds-ratio preference term into the SFT loss, so no reference model is needed at all.
- **"Now implement IPO."** Replace the logsigmoid with a squared loss against a target margin, which removes DPO's tendency to overfit a deterministic preference.
- **"Now do KTO."** Learn from single thumbs-up/thumbs-down labels instead of pairs, using a reference point in place of the rejected response.
- **"Add length normalization."** Divide sequence log-probabilities by token count. This is a real and contested choice — it fights DPO's length bias and changes what the objective means.

# Further Reading

- [Direct Preference Optimization](https://arxiv.org/abs/2305.18290) — work through the derivation by hand once; it is four pages and it is worth it.
- [DeepSeekMath](https://arxiv.org/abs/2402.03300) — GRPO, including the k3 KL estimator.
- [Approximating KL Divergence](http://joschu.net/blog/kl-approx.html) — Schulman's short note on why k3 is the right estimator. Frequently cited in interviews.
- [TRL](https://github.com/huggingface/trl) — reference implementations of DPO, KTO, ORPO, PPO, and GRPO, all readable.
