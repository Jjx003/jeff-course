# Debugging Guide

Run this list in order. It is roughly the order of how much search space each step eliminates.

**1. Is the initial loss near `ln V`?** If not, stop and fix that. Nothing downstream is meaningful.

**2. Can it overfit one batch?** If a correct model cannot memorize eight tokens in 300 steps, the bug is in the model or the optimizer.

**3. Does the causality test pass?** Perturb a future token, check earlier logits.

**4. Are the shapes right at every stage?** `(B,S)` ids, `(B,S,d)` hidden, `(B,S,V)` logits.

**5. Is the loss shift applied exactly once?** Loss stuck around 3–4 on a task that should reach 0 usually means a double shift.

# Common Failures

**Loss starts at `ln V` and stays there.** Gradients are not flowing. Check that parameters are in the optimizer, that you called `zero_grad`, and that there is no stray `no_grad` or `detach`.

**Loss drops to near zero in three steps.** Too good. The model is reading the label — usually a mask problem or labels that equal inputs.

**Loss goes to `nan`.** Learning rate too high, or unstable softmax. Print the grad norm each step; if it spikes before the `nan`, clip.

**Generation repeats one token forever.** Under greedy decoding on an undertrained model this is normal. On a model that memorized its training sequence it means the generation loop is not appending, or is re-encoding the prompt each step.

**Everything is correct but the model is worse than it should be.** Look for the invisible bugs: missing final norm, a shared norm module across both sublayers, missing residual scaling at init.

# Rapid-Fire Answers

**"How do you sanity check a new LM implementation?"**
> Initial loss should be `ln V`. Then overfit a single batch to near-zero loss. Those two checks catch most structural bugs in about a minute, before any real compute is spent.

**"Why is the final norm needed?"**
> In a pre-norm model the residual stream grows in magnitude with depth, so without a final normalization the logits carry an arbitrary depth-dependent scale.

**"What does weight tying do to the backward pass?"**
> The tied tensor receives gradient from both the embedding lookup and the output projection, and those two contributions sum.

**"Why scale the output projections by `1/sqrt(2L)`?"**
> `2L` sublayers each add into the residual stream, so without the correction its variance grows linearly in depth. GPT-2 introduced the fix and it stuck.

# Further Reading

- [nanoGPT](https://github.com/karpathy/nanoGPT) — read `model.py` in full. It is the reference for everything in this module.
- [Let's build GPT: from scratch, in code, spelled out](https://www.youtube.com/watch?v=kCc8FmEb1nY) — if any of this is still fuzzy, two hours here fixes it.
- [Language Models are Unsupervised Multitask Learners](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf) — the GPT-2 paper, source of the `1/sqrt(2L)` initialization.
