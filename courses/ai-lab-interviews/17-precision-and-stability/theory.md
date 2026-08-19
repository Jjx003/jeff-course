# The Formats

| Format | Bits | Exponent | Mantissa | Max value | Relative precision |
|---|---|---|---|---|---|
| fp32 | 32 | 8 | 23 | $3.4\times10^{38}$ | $1.2\times10^{-7}$ |
| tf32 | 19 stored in 32 | 8 | 10 | $3.4\times10^{38}$ | $9.8\times10^{-4}$ |
| bf16 | 16 | 8 | 7 | $3.4\times10^{38}$ | $7.8\times10^{-3}$ |
| fp16 | 16 | 5 | 10 | $6.5\times10^{4}$ | $9.8\times10^{-4}$ |
| fp8 E4M3 | 8 | 4 | 3 | $448$ | $1.25\times10^{-1}$ |
| fp8 E5M2 | 8 | 5 | 2 | $5.7\times10^{4}$ | $2.5\times10^{-1}$ |

Relative precision here is machine epsilon, $2^{-m}$ for $m$ mantissa bits, which is what torch.finfo reports for each dtype.

## Why bf16 beat fp16

Both are 16 bits. They spend them differently.

**fp16** gives you 10 mantissa bits — better precision than bf16 — but only 5 exponent bits, so the representable range is roughly $6\times10^{-8}$ to $65504$. Deep-network gradients live near the bottom of that range and underflow to zero.

**The fp16 fix was loss scaling.** Multiply the loss by a large constant $S$ (say $2^{15}$) before backward, so every gradient is scaled up into representable range, then divide by $S$ before the optimizer step. Dynamic loss scaling adjusts $S$ automatically: raise it when things are fine, halve it and skip the step whenever an `inf` appears. It works, and it is one more thing to get wrong.

**bf16** shares fp32's 8-bit exponent, so for practical purposes anything representable in fp32 is representable in bf16 — no underflow, no overflow, no loss scaling. (Strictly the range is a hair narrower at both ends: bf16 tops out at $3.3895\times10^{38}$ against fp32's $3.4028\times10^{38}$, and its smallest subnormal is $9.2\times10^{-41}$ against fp32's $1.4\times10^{-45}$. Neither matters for training.) The cost is 7 mantissa bits, about 2–3 decimal digits.

Two things follow that interviewers like to hear:

- **Casting fp32 to bf16 is nearly free** — truncate the mantissa, keep the exponent. That is also why bf16 and fp32 interconvert so cheaply in hardware.
- **The precision loss is survivable because SGD is noisy anyway.** Gradient noise from minibatching dwarfs bf16 rounding. What is *not* survivable is precision loss in **reductions**, where errors accumulate across thousands of terms — which is exactly where fp32 is retained.

## What mixed precision actually keeps in fp32

The standard recipe:

- **fp32 master weights.** Updates are often much smaller than the weights. In bf16 with 7 mantissa bits, adding $10^{-4}$ to $1.0$ rounds to $1.0$ — the update simply vanishes. The master copy exists so small updates accumulate.
- **fp32 optimizer moments.** Same argument.
- **bf16 forward and backward.** This is where the speed comes from — tensor cores and halved memory traffic.
- **fp32 reductions.** Norm statistics, softmax denominators, and loss reductions.

Net memory: 4 (master) + 2 (working) + 2 (gradients) + 8 (moments) = **16 bytes per parameter**, exactly the same as pure fp32. Mixed precision buys throughput, not memory. Say that out loud; it surprises people.

## fp8

Two formats because one set of trade-offs does not fit both directions:

- **E4M3** — more mantissa, max 448. Used for forward-pass activations and weights, which are bounded.
- **E5M2** — more exponent, max 57344. Used for gradients, which have much wider dynamic range.

fp8 training needs **scaling factors** maintained alongside the tensors, because 4 exponent bits cannot cover the range on their own. The original recipe (NVIDIA's Transformer Engine) used per-tensor delayed scaling — one scale per tensor, updated from a history of recent maxima. That bookkeeping is what makes fp8 training hard, and why it took several hardware generations to become practical.

The state of the art moved to **finer-grained scales**. DeepSeek-V3 — the first frontier-scale model with a public account of fp8 pretraining — used block-wise scaling (per 128×128 weight block, per 1×128 activation tile) with fp32 accumulation. Blackwell-generation hardware bakes the same idea in as **microscaling (MX) formats** — MXFP8 and MXFP4 attach a shared power-of-two scale to every block of 32 elements, so the scaling that used to be software bookkeeping is now a hardware datatype.

**Be careful about *why*, because the obvious answer is wrong and interviewers do check.** The story you will hear is "one scale per tensor means a single outlier crushes the resolution of everything else." That is emphatically true of **integer** formats, and it is the entire reason int8 quantization lives or dies on block size. It is *not* how floating point fails: fp8 carries a private exponent per element, so its relative precision is roughly scale-invariant, and a tensor-wide scale set by a 1000× outlier still leaves ordinary values with their full three mantissa bits.

![Two panels. Left: mean relative error against scaling block size with a 100x outlier present, int8 falling steeply from 48% at per-tensor to 4% at block 32 while fp8 stays flat near 2.2%. Right: error against outlier magnitude from 1x to 1000x, int8 per-tensor climbing to nearly 100% and int8 block-128 to 15%, while both fp8 curves stay flat.](/courses/ai-lab-interviews/fp8-scaling-granularity.svg)

So what does fine-grained fp8 scaling actually buy? Two things, neither of them the outlier story:

1. **Range, not resolution.** E4M3 bottoms out at $2^{-9}$. A scale chosen for the block maximum pushes the smallest values toward that floor, and anything under it flushes to zero. Smaller blocks keep each group's values in the middle of the range.
2. **Accumulation.** This is the real fight. Tensor cores accumulate fp8 products at reduced internal precision, so long dot products lose bits regardless of how well you scaled the inputs. DeepSeek-V3's answer was to promote partial sums into fp32 CUDA cores at a fixed interval — the block structure exists partly to make that promotion cheap.

If you can say "for int8 it is about outliers eating the range; for fp8 it is about the accumulator," you are ahead of the standard answer.

For **inference**, fp8 is much easier — weights are static, so scales can be computed offline — which is why fp8 serving arrived well before fp8 training and is now routine for production deployments.

# Stability

## Max-subtracted softmax

Softmax is invariant to a constant shift:

$$\mathrm{softmax}(x)_i = \frac{e^{x_i - c}}{\sum_j e^{x_j - c}}$$

for any $c$. Choosing $c = x_{\max}$ makes the largest exponent $e^0 = 1$, so nothing overflows, and the denominator is at least 1, so nothing divides by zero.

Without it, in float32, $e^x$ overflows at around $x \approx 88$. Attention logits reach that easily in a large model, particularly if someone forgot the $1/\sqrt{d_k}$.

## log-sum-exp

$$\log\sum_i e^{x_i} = x_{\max} + \log\sum_i e^{x_i - x_{\max}}$$

Same trick, and it is what lets you compute a log-probability without materializing the probability. Compare:

- `log(softmax(x))` — computes a probability that may be $10^{-30}$, then takes its log. The small value has already lost most of its significant digits.
- `x - logsumexp(x)` — never forms the small number at all.

This is why `F.log_softmax` exists as a separate function and why `F.cross_entropy` takes logits.

## Online softmax

The naive stable softmax needs two passes: one to find $x_{\max}$, one to accumulate the denominator. The online version fuses them.

Maintain a running maximum $m_k$ and a running denominator $d_k = \sum_{j\le k}e^{x_j - m_k}$. On seeing $x_{k+1}$:

$$m_{k+1} = \max(m_k, x_{k+1})$$

$$d_{k+1} = d_k \cdot e^{m_k - m_{k+1}} + e^{x_{k+1} - m_{k+1}}$$

The correctness argument, which is worth being able to give:

$$d_{k+1} = \sum_{j=1}^{k+1}e^{x_j - m_{k+1}} = e^{x_{k+1}-m_{k+1}} + \sum_{j=1}^{k}e^{x_j - m_k}e^{m_k - m_{k+1}} = e^{x_{k+1}-m_{k+1}} + d_k e^{m_k-m_{k+1}}$$

The factor $e^{m_k - m_{k+1}}$ **rescales the accumulated sum** to the new maximum, and equals 1 whenever the maximum has not changed.

**Why it matters:** this recurrence is what lets FlashAttention stream key/value tiles without ever materializing the full score row. The same rescaling applies to the weighted output accumulator, not just the denominator — which is the extra step from "online softmax" to "FlashAttention".

## Other stability practices

- **Norms in fp32.** Covered in the RMSNorm module; the reason is reduction error.
- **QK-norm.** Normalizing Q and K before the score matmul bounds attention logits and prevents the entropy collapse behind some large-model loss spikes.
- **Gradient clipping.** Bounds the damage a single bad batch can do.
- **`eps` inside the square root.** $\sqrt{\sigma^2 + \epsilon}$, not $\sqrt{\sigma^2} + \epsilon$. Different behavior for small inputs, and a real bug in a few implementations.
- **Chunked cross-entropy.** The $b\times S\times V$ logit tensor in fp32 is often the largest activation in a training step; computing the loss in chunks avoids materializing it all at once.
