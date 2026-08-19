# When You Get Stuck

**Probe 1 fails.** Print the mask. `causal_mask(6).int()` shows you the answer immediately. Which triangle should be `True`?

**Probe 2's shape check passes but the other two fail.** The shape is right and the semantics are wrong. Ask which axis the projection laid the heads out along.

**Probe 3 fails but the shapes are fine.** Compare your attention to the fused kernel on a two-element input by hand. What single scalar stands between them?

**Probe 4 fails after 1–3 pass.** The kernel is right, so the bug is in what gets fed to it. Three tensors go in. Which of them should never carry position?

**Probe 5 fails.** The RMS entering the head is not 1. Something that normalizes is missing. Read `__init__`, then read `forward`, and compare the two lists.

**Probe 6 fails.** This probe uses no model at all — only hand-built logits and the loss function. Read `lm_loss` and ask: which position predicts which token?

**Probe 9 passes while others fail.** Sit with that for a second. It is the lesson of the module.

# The Trap

One of the bugs makes the model reach a **lower** loss than the correct implementation, and lets probe 9's "final loss below 0.05" pass.

When the objective is unshifted, next-token prediction becomes copy-the-input. That is trivially learnable — the model only has to route the current embedding to the output — so the loss collapses to essentially zero within a few dozen steps. Meanwhile greedy generation produces the same token forever, because the model has learned to predict what it just saw.

Two things to take from that:

1. **A falling loss is not evidence of a correct implementation.** It is evidence that *something* is learnable.
2. **Always pair a loss check with a behavioral check.** Generation, causality, and eval on held-out data are what catch an objective that is learning the wrong task.

# Rapid-Fire Answers

**"Your model's loss looks great but the samples are garbage. What do you check?"**
> Whether the objective is the task I think it is. First the label shift — test the loss function alone with oracle logits. Then causality — perturb a future token and check earlier outputs. Both are bugs where a lower loss is the symptom, not the refutation.

**"How would you verify a transformer implementation you did not write?"**
> A ladder of probes from local to global: pure functions against known invariants, kernels against `scaled_dot_product_attention`, the model against `ln V` at init, then behavioral checks for causality and the shift, then overfitting one batch. Each level is only meaningful once the ones above it pass.

**"The loss plateaus at 3.5 and will not move."**
> A plateau well above `ln V` but well below sensible usually means the objective is partly unlearnable — a double shift, or labels misaligned with inputs. I would test the loss function in isolation with hand-built logits before touching the model.

# Further Reading

- [A Recipe for Training Neural Networks](http://karpathy.github.io/2019/04/25/recipe/) — the canonical essay on this exact method. Read it once a year.
- [nanoGPT](https://github.com/karpathy/nanoGPT) — the known-good implementation to diff against when your own goes wrong.
- [The Annotated Transformer](https://nlp.seas.harvard.edu/annotated-transformer/) — useful as a second reference implementation with different conventions, which is itself a good way to find your assumptions.
