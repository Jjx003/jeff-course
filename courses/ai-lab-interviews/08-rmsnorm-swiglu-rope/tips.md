# Debugging Guide

**RMSNorm output is off by a constant factor.** You divided by the sum instead of the mean, or by `d` instead of `sqrt(d)`. Sanity check: for input of all ones, RMSNorm returns all ones.

**The bf16 comparison shows no improvement from the upcast.** Your upcast is not actually reaching the reduction — check that `.float()` happens before `.pow(2).mean()`, not after.

**SwiGLU parameter count is off by a third.** You sized all three matrices at `4d` instead of `8d/3`, or forgot that `w_down` is `(d_ff, d)` not `(d, d_ff)`.

**RoPE changes the vector norm.** Then it is not a rotation. Usually a sign error: the correct pair is `(x1*cos - x2*sin, x1*sin + x2*cos)`. Flipping a sign gives a reflection, which does not preserve the relative property.

**The relative-position test fails.** Check you applied the *same* cache to Q and K, and indexed it by absolute position for each. If you index Q at position `m` and K at position `0` regardless, the test fails in exactly this way.

**The relative test passes but so does everything, including a no-op RoPE.** That is what the position-sensitivity check exists for: attention scores must actually change with position. A RoPE that returns its input unchanged is trivially "relative".

# Rapid-Fire Answers

**"Why RMSNorm over LayerNorm?"**
> Drops mean subtraction and bias. Re-scaling is what stabilizes training; re-centering was not earning its cost. Saves a reduction pass and `d` parameters per norm. Compute the statistic in fp32 even in a bf16 model.

**"Why is the SwiGLU hidden dim 8d/3?"**
> Three matrices instead of two. `3 * d * d_ff = 8d^2` gives `d_ff = 8d/3`, matching the parameter count of the 4x ReLU FFN it replaces. Rounded up to a multiple of 256 in practice — that is where Llama's 11008 comes from.

**"How does RoPE work?"**
> Rotate Q and K in 2-D channel pairs by an angle proportional to position. Rotations are orthogonal, so `R_m^T R_n = R_{n-m}` and the dot product depends only on the offset. Relative by construction, no parameters, nothing added to the residual stream.

**"How do you extend a 4k-context model to 32k?"**
> Position interpolation, NTK-aware base scaling, or YaRN, each with a little continued pretraining. The real limit is that the model never saw genuinely long-range dependencies in training, so benchmarks that need them still degrade. New models mostly avoid the problem: a large base from the start (Llama 3: 500k) plus a staged long-context phase.

# Further Reading

- [RoFormer](https://arxiv.org/abs/2104.09864) — RoPE.
- [GLU Variants Improve Transformer](https://arxiv.org/abs/2002.05202) — Shazeer's SwiGLU note, three pages and worth reading in full.
- [Root Mean Square Layer Normalization](https://arxiv.org/abs/1910.07467)
- [YaRN: Efficient Context Window Extension](https://arxiv.org/abs/2309.00071)
- [Llama `model.py`](https://github.com/meta-llama/llama/blob/main/llama/model.py) — the reference implementation of all three. Note it uses the **interleaved** convention, via complex arithmetic over adjacent channel pairs; HuggingFace `transformers` uses split-half, which is why its conversion script permutes Q and K.
