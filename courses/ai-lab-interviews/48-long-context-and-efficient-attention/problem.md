# Long Context and Efficient Attention

Module 06 gave you one paragraph each on MLA, sliding windows, and RoPE base scaling. This module is the version you would want if the interviewer keeps pulling.

It is optional. Take it if you are interviewing anywhere that serves long contexts, or if "how would you make this handle a million tokens" is a question you would rather not improvise.

## Three separate problems

People collapse these into "long context is hard." They have different causes and different fixes, and separating them is most of the skill.

| Problem | Grows as | What fixes it |
|---|---|---|
| **Attention compute** | $O(S^2)$ per layer | sparsity, sliding windows, linear-attention hybrids |
| **KV cache memory** | $O(S)$ per layer, per sequence | GQA, MLA, quantization, windowed layers |
| **Positional generalization** | doesn't grow — breaks | RoPE base scaling, YaRN, long-context training |

FlashAttention fixes *none* of them. It removes the $O(S^2)$ **memory** of materializing the score matrix — which was the binding constraint in 2022 — but the FLOPs are still quadratic and the cache is still linear. Saying "we use FlashAttention" in answer to "how do you handle long context" is a common and visible mistake.

## What gets asked

- Walk me through MLA. Why does RoPE need special handling in it?
- Why is the KV cache the binding constraint at long context rather than the attention FLOPs?
- What is the difference between extending a trained model's context and training for it?
- Sliding-window attention loses information from beyond the window. Why does it work anyway?
- What are attention sinks and why does evicting the first token break everything?
- When would you reach for a sparse pattern over a hybrid stack?

## The framing to have ready

At 4k tokens, attention is a rounding error and the cache is small: nothing here matters. At 128k, the cache dominates your memory budget and attention is a serious fraction of your FLOPs. At 1M, both are the whole problem and you need architectural help, not tuning. Knowing *where the regime changes* — and being able to compute the crossover, as module 13 taught you — is more useful than knowing every technique's name.
