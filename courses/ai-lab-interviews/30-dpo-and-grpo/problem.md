# DPO and GRPO Losses

"Here is the paper's equation. Implement it." is a standard ML coding prompt, and these two are the ones currently being asked.

Both are short. Neither requires a model — you work directly on log-probabilities, which is exactly how you would prototype them anyway, and it means you can verify the *properties* of each loss rather than just that it runs.

## What to implement

1. `sequence_logprob` — sum per-token log-probabilities, with a mask.
2. `dpo_loss` — the implicit rewards and the logsigmoid objective.
3. `grpo_advantages` — group-relative normalization.
4. `grpo_loss` — the clipped surrogate plus an optional KL penalty.

## What the script verifies

Not just numerical agreement — the **properties each loss is supposed to have**:

- **DPO at initialization gives exactly $\ln 2$.** When the policy equals the reference, the implicit rewards are equal and the model is exactly indifferent. If your loss does not start at 0.6931, something is wrong.
- **DPO is invariant to a constant shift** applied to both log-probabilities. This is the same fact that makes the partition function cancel in the derivation.
- **DPO's gradient is equal and opposite** on the chosen and rejected responses. That is not itself the "DPO drags both down" effect — it is the *reason* for it: the objective constrains only the gap, so nothing anchors either absolute log-probability.
- **A GRPO group with uniform rewards produces zero advantage**, so a prompt that is uniformly too easy or too hard contributes no gradient at all.
- **The clipped ratio caps a positive-advantage sample's gain at $1+\epsilon$**, even when the policy moved by a factor of 7 — while the same move on a negative-advantage sample is *not* clipped, because the `min` keeps the full penalty. The one-sidedness is checked, not just the cap.
- **The k3 KL estimator is zero at equality and positive in both directions**, unlike the naive log-ratio estimator.

## Why properties rather than reference values

Because in an interview you will not have a reference implementation to diff against. What you will have is the ability to say *"let me check that this gives ln 2 when the policy equals the reference"* — and that sentence is worth more than a correct implementation delivered silently.
