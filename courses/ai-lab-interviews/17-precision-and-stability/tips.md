# Rapid-Fire Answers

**"fp16 versus bf16?"**
> Same 16 bits, spent differently. fp16: 5 exponent, 10 mantissa, max 65504 — better precision, and gradients underflow, which is why it needed loss scaling. bf16: 8 exponent (fp32's), 7 mantissa — worse precision, full fp32 range, so no loss scaling and no overflow surprises. Casting fp32 to bf16 is a mantissa truncation.

**"What does mixed precision keep in fp32?"**
> Master weights, optimizer moments, and reductions. Matmuls run in bf16. Net 16 bytes per parameter, which is the same as pure fp32 — mixed precision buys throughput, not memory.

**"Why fp32 master weights?"**
> With 7 mantissa bits, adding an update of `1e-4` to a weight of `1.0` rounds back to `1.0`. The update disappears. The master copy is what lets small updates accumulate.

**"Why subtract the max in softmax?"**
> Softmax is shift-invariant. Subtracting the row max makes the largest exponent `e^0 = 1`, so nothing overflows, and the denominator is at least 1, so nothing divides by zero. Without it, `exp` overflows around 88 in float32.

**"Derive the online softmax recurrence."**
> Track a running max `m` and a running denominator `d`. On a new element: `m' = max(m, x)`, `d' = d * exp(m - m') + exp(x - m')`. The exponential factor rescales the accumulated sum to the new maximum, and is 1 when the max is unchanged. That fuses the two passes into one, which is what lets FlashAttention stream tiles.

**"What is fp8 training and why is it hard?"**
> Two formats — E4M3 for forward, E5M2 for gradients — because 4 exponent bits cannot cover gradient range. It needs per-tensor scaling factors maintained across steps, usually with delayed scaling from a history of recent maxima. Inference is much easier because weights are static and scales can be computed offline.

# Traps

- **Saying bf16 is "less precise so it is worse".** Say what it trades: precision for range, which removes an entire class of failure.
- **Claiming mixed precision halves memory.** It does not — the fp32 master copy and moments keep you at 16 bytes per parameter.
- **Forgetting that reductions stay in fp32.** That is where the precision actually matters.
- **Confusing loss scaling with gradient clipping.** Loss scaling moves gradients into representable range for fp16; clipping bounds their magnitude for stability. Unrelated problems.
- **Saying softmax needs the max subtraction "for stability"** and stopping there. Say *which* instability: `exp` overflow at around 88 in fp32.

# Further Reading

- [Mixed Precision Training](https://arxiv.org/abs/1710.03740) — the original loss-scaling paper.
- [FP8 Formats for Deep Learning](https://arxiv.org/abs/2209.05433) — E4M3, E5M2, and the scaling machinery.
- [Online normalizer calculation for softmax](https://arxiv.org/abs/1805.02867) — the recurrence, in three pages.
- [FlashAttention](https://arxiv.org/abs/2205.14135) — where the recurrence is put to work.
- [What Every Computer Scientist Should Know About Floating-Point Arithmetic](https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html) — the classic, if you want the foundations properly.
