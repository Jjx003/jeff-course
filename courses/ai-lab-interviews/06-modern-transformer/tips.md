# The Whiteboard Version

If you can write this from memory, you can answer most architecture questions by pointing at it.

```
x = embed(ids)                        # (B, S, d)
for layer in layers:
    h = rmsnorm(x)
    q, k, v = Wq(h), Wk(h), Wv(h)     # GQA: k, v are narrower
    q, k = rope(q, pos), rope(k, pos) # never applied to v
    k, v = repeat_kv(k, v, groups)
    a = softmax(q @ k.T / sqrt(dh) + causal_mask) @ v
    x = x + Wo(merge_heads(a))
    x = x + swiglu(rmsnorm(x))
x = rmsnorm(x)                        # final norm — pre-norm requires it
logits = x @ embed.weight.T           # if tied
```

# Rapid-Fire Answers

**"Why divide by sqrt(d_k)?"**
> The dot product of two unit-variance vectors of length `d_k` has variance `d_k`. Without scaling, the logits grow with head dimension, softmax saturates, and the gradient vanishes. The division restores unit variance.

**"Pre-norm or post-norm, and why?"**
> Pre-norm. It keeps the residual stream a clean additive path so gradients reach early layers, which is what makes 100-layer stacks trainable. The price is a growing residual magnitude, so you need a final norm before the head.

**"RMSNorm versus LayerNorm?"**
> RMSNorm drops mean subtraction and the bias. Re-scaling is what mattered; re-centering was not doing work. Saves a reduction and `d` parameters per norm. Compute it in fp32 even in a bf16 model.

**"Ways of encoding position?"**
> Four families: sinusoidal absolute, learned absolute, relative bias (T5 buckets, ALiBi slopes), and rotary. RoPE is the default — relative by construction, no parameters, applied to Q and K only, and extensible to longer context by scaling the base or interpolating positions.

**"MHA, MQA, GQA?"**
> Decoding is memory-bandwidth bound and the KV cache is what you read every step. MQA collapses to one KV head — an `H`-fold saving but real quality loss. GQA groups query heads over a handful of KV heads, typically 8, and recovers essentially all the quality at most of the saving.

**"GQA versus MLA?"**
> Two attacks on the same KV-cache bottleneck. GQA shares K and V across groups of query heads — cache scales with `G/H`, essentially free at `G=8`. MLA compresses K and V into one low-rank latent per token and caches only that; the up-projections get absorbed into the query and output projections at inference, and a small decoupled rotary key carries position. DeepSeek-V3 caches 576 elements per token per layer against 2048 for GQA-8 — a bigger saving than GQA, with reported quality at or above MHA, at the cost of extra projections and implementation complexity.

**"How many parameters in a transformer?"**
> Roughly `12 * L * d^2` plus `V * d` for embeddings. `4d^2` attention, `8d^2` FFN per layer.

# Traps

- **Applying RoPE to V.** Position should determine what you attend to, not what you retrieve. Only Q and K.
- **Masking after the softmax.** The rows stop summing to 1.
- **Forgetting the final norm** in a pre-norm model. Trains, but the logits are misscaled and quality is quietly worse.
- **`view` after `transpose` without `contiguous`.** Transpose only changes strides; `view` needs contiguous memory. Use `reshape` if you do not want to think about it, but know why it works.
- **Saying "attention is O(n^2) so long context is impossible."** It is quadratic in *compute*, but the binding constraint at inference is usually the KV cache, which is linear. Know which one you mean.

# Further Reading

- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) and [The Illustrated GPT-2](https://jalammar.github.io/illustrated-gpt2/)
- [RoFormer: Enhanced Transformer with Rotary Position Embedding](https://arxiv.org/abs/2104.09864) — the RoPE paper.
- [GQA: Training Generalized Multi-Query Transformer Models](https://arxiv.org/abs/2305.13245)
- [Root Mean Square Layer Normalization](https://arxiv.org/abs/1910.07467)
- [nanoGPT](https://github.com/karpathy/nanoGPT) — read `model.py` end to end. It is 300 lines and it is the mental model interviewers are testing.
