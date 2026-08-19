# Debugging Guide

**Cached and uncached outputs diverge after the first token.** The RoPE offset. Print it every step; it should equal the number of tokens already in the cache.

**They diverge only for long generations.** Also the offset, or a mask that is aligned to the left edge of the key sequence instead of the right.

**Everything is `nan` after top-p.** An all-`-inf` row. You removed every token because one token's probability already exceeded `p`. Force the top token to survive.

**Top-p retains slightly less mass than `p`.** The shift. Compare `cumulative - probs >= p`, not `cumulative >= p`, so the token that crosses the threshold is kept.

**The cache grows faster than expected.** You are caching after the `repeat_interleave` to `H` heads instead of before. Store `G` heads and expand on read, or GQA saves you nothing.

**Sampling frequencies do not match the filtered distribution.** Check the order: temperature, then truncation, then normalize. Truncating before applying temperature measures a distribution you are not sampling from.

# Rapid-Fire Answers

**"Add a KV cache to this attention."**
> Concatenate past K and V along the sequence axis, apply RoPE at the absolute offset — which is the cache length, not zero — and skip the causal mask when the query length is 1, because position `t` may legitimately attend to everything cached. Store `G` KV heads and expand to `H` after reading.

**"What breaks if you forget the RoPE offset?"**
> Every generated token believes it is at position 0. It runs, it produces fluent-looking text, and it is wrong — increasingly so as the sequence grows. Nothing in the shapes or the loss will tell you.

**"Why top-p rather than top-k?"**
> A fixed `k` is too permissive when the model is confident and too restrictive when it is not. Nucleus sampling picks a cutoff from the shape of each distribution. Concretely: at `p = 0.9`, a confident distribution keeps one token and an uncertain one keeps five.

**"How would you make this production-ready?"**
> Preallocate the cache to the maximum length and write into slices rather than concatenating each step. Batch it, with per-sequence lengths. Then paged attention, so the cache lives in fixed-size blocks with a block table — that removes fragmentation and gives prefix sharing for free.

# Variations to Expect

- **"Now batch it."** Sequences have different lengths, so you need a padding mask and per-sequence positions — which is precisely where fully-masked rows and `nan` come from.
- **"Now add speculative decoding."** Verify $\gamma+1$ positions in one forward pass; the mask expression with `diagonal=T-s` already handles a multi-token query.
- **"Now implement prefix sharing."** Two sequences with a common prompt should share cache blocks until they diverge. This is the copy-on-write idea behind paged attention.
- **"Now quantize the cache."** int8 per-token scales. Note it must be done at runtime, unlike weight quantization, and that keys are more outlier-prone than values.

# Further Reading

- [Efficiently Scaling Transformer Inference](https://arxiv.org/abs/2211.05102)
- [PagedAttention / vLLM](https://arxiv.org/abs/2309.06180)
- [The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751) — nucleus sampling.
- [Hugging Face's generation utilities](https://github.com/huggingface/transformers/blob/main/src/transformers/generation/logits_process.py) — worth reading once to see how many warpers exist and in what order they are applied.
