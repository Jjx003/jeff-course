# Debugging Guide

**Online denominator disagrees with the two-pass version.** Almost always the rescale factor. It is `exp(m_old - m_new)`, and it multiplies the *accumulator*, not the new term. Getting the sign backwards gives `exp(m_new - m_old) >= 1`, which grows without bound.

**Online version returns `nan` on the first element.** Initialize `m = -inf` and `d = 0`. Then `exp(-inf - x) = 0` and the first update is clean. Initializing `m = 0` breaks for all-negative inputs.

**The weighted-sum accumulator drifts.** The accumulator and the denominator must be rescaled by the *same* factor at the *same* time. Rescaling one and not the other gives an answer that looks approximately right, which is worse than obviously wrong.

**`log_softmax` matches but is slower than expected.** Fine — this exercise is about numerics, not speed. In production you would call `F.log_softmax`, which fuses the whole thing.

**Check 7 surprises you.** The point is the *accumulator* dtype, not the tensor dtype. `torch.sum` on a bf16 tensor is nearly exact because torch upcasts the accumulator internally; the explicit bf16-accumulator loop is what a naive handwritten kernel does, and it stalls once the running sum is ~256x the incoming term.

# The Whiteboard Version

Rehearse this until you can produce it while talking:

```
m = -inf, d = 0
for x in stream:
    m_new = max(m, x)
    d = d * exp(m - m_new) + exp(x - m_new)
    m = m_new
softmax(x_i) = exp(x_i - m) / d
```

Then the extension, out loud: *"For attention I also carry an output accumulator and rescale it by the same factor, so I get the weighted sum in one pass without ever materializing the score row. That is FlashAttention."*

# Rapid-Fire Answers

**"Why does softmax subtract the max?"**
> Softmax is shift-invariant, so it changes nothing mathematically. Numerically it caps the largest exponent at `e^0 = 1` and floors the denominator at 1. Without it, `exp` overflows around 88 in float32.

**"Why `x - logsumexp(x)` rather than `log(softmax(x))`?"**
> The naive form materializes a probability that can underflow to exactly zero for a low-probability token, and then `log(0) = -inf`. The information is lost in the intermediate value, not in the log.

**"What does FlashAttention actually do?"**
> Streams key/value tiles through the online softmax recurrence, rescaling an output accumulator alongside the denominator, so the `(B,H,S,S)` score tensor is never materialized. The memory footprint drops from `O(S^2)` to `O(S)`, and HBM traffic falls by a large constant factor rather than becoming linear. The FLOP count is unchanged and the output is exact. The backward pass recomputes scores rather than storing them.

**"Why compute norms in fp32 in a bf16 model?"**
> The accumulator. With 8 significand bits, once a running bf16 sum is about 256x the incoming term, adding it changes nothing — summing 8192 ones in bf16 gives exactly 256. A single multiply in bf16 is fine; a long reduction with a bf16 accumulator silently stalls. Library reductions and tensor-core matmuls already accumulate in fp32; the rule is for the kernels you write.

# Further Reading

- [Online normalizer calculation for softmax](https://arxiv.org/abs/1805.02867) — three pages, the whole recurrence.
- [FlashAttention](https://arxiv.org/abs/2205.14135) and [FlashAttention-2](https://arxiv.org/abs/2307.08691)
- The **Model Optimization Systems** track has a full module implementing tiled attention with this recurrence, including causal tile skipping.
