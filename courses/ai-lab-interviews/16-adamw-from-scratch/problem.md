# AdamW From Scratch

"Implement AdamW" is a real, common ML coding prompt. It is short enough to finish inside an interview and specific enough that a vague understanding fails immediately.

You will write the optimizer, a warmup-plus-cosine schedule, and global gradient clipping, and the script will hold all three against torch's own implementations.

## What to implement

1. `AdamW.step` — moments, bias correction, decoupled decay, the update.
2. `lr_at_step` — linear warmup, then cosine decay to a floor.
3. `clip_grad_norm` — global norm, rescale if it exceeds the threshold.

## What the script checks

- **Bit-level agreement with `torch.optim.AdamW`** over 25 steps in float64 — both the loss trace and the final parameters.
- **That decoupled decay is genuinely different** from `torch.optim.Adam(weight_decay=...)`, which folds the same $\lambda$ into the gradient. The gap it reports is the concrete answer to "does the Adam-versus-AdamW distinction actually matter".
- **Bias correction**, via a lovely property: on step one, the update is *exactly* the learning rate, whatever the gradient was — because $\hat{m}/\sqrt{\hat{v}} = g/|g| = 1$. Without the correction it would be $\sqrt{(1-\beta_2)}/(1-\beta_1)$ times smaller.
- **The schedule** hits zero at step 0, peaks exactly at the end of warmup, is monotone after it, and floors correctly.
- **Clipping** produces the target norm, leaves small gradients untouched, and — the check that matters — leaves the *direction* of every tensor unchanged, which is the difference between global and per-tensor clipping.

## The bar

Fifteen minutes for `AdamW.step` from an empty file. The three things that go wrong under pressure: `t` starting at 0, the decay applied to the gradient instead of the parameter, and forgetting that `v` accumulates the element-wise square.
