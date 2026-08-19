# A Whole Language Model

You have attention, RMSNorm, SwiGLU, and RoPE. This module assembles them into a model that trains.

The last mile is where the interesting bugs live: the residual structure, the label shift, weight tying, and the initialization sanity check that tells you within one step whether anything is wrong at all.

## What to implement

1. `TransformerBlock.forward` — the pre-norm residual structure.
2. `TransformerLM.forward` — embed, run the stack, final norm, tied output head.
3. `lm_loss` — next-token cross-entropy with the correct shift.
4. `generate` — greedy decoding, no cache (the cache comes in module 26).

## What the script checks

- **Shapes** — logits are `(B, S, V)`.
- **The initialization check.** Loss at step 0 must be close to $\ln V$. Any model whose initial loss is far from $\ln V$ has something structurally wrong, and this is the fastest diagnostic in existence.
- **Weight tying** — the gradient reaching the tied tensor is verified to be the *sum* of the embedding-lookup path and the output-projection path, by isolating each with a `detach()` and adding them back. That is the branch-sum rule from module 2, showing up in production code.
- **Causality** — perturbing a future token leaves earlier logits untouched.
- **The shift** — predicting position $t$ from positions $\le t$, verified by checking that the loss on shuffled labels is much worse.
- **It learns** — 300 steps of AdamW on one fixed sequence drives the loss near zero and reproduces the sequence exactly under greedy decoding.

## The check worth internalizing

$$L_{\text{init}} \approx \ln V$$

At initialization the model has no information, so its best guess is uniform over the vocabulary, and the cross-entropy of a uniform distribution over $V$ classes is $\ln V$. For $V = 50257$ that is about 10.8; for $V = 32000$, about 10.4.

If your initial loss is 15, the output layer is badly scaled. If it is 2, you are leaking the answer — a broken causal mask or a missing shift. Interviewers ask "how do you know your model is set up correctly before you spend a week of compute" and this is the answer.
