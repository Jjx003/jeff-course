# Debugging Guide

**Shapes are right, values are wrong.** Check the transpose in the score matmul: it is `k.transpose(-2, -1)`, giving `(B,H,S,dh) @ (B,H,dh,S) = (B,H,S,S)`. Using `k.T` on a 4-D tensor reverses *all* dimensions and is wrong.

**Causality test fails but the mask looks right.** You masked after the softmax, or used `triu` instead of `tril`, or excluded the diagonal.

**Output is `nan`.** A fully-masked row. With a pure causal mask this cannot happen — row 0 always has one allowed key — but it does happen once you add left padding.

**`view` raises "view size is not compatible with input tensor's size and stride".** You transposed and then viewed. Insert `.contiguous()` or use `.reshape()`.

**GQA matches at `G == H` but not below.** Almost always `repeat` where you needed `repeat_interleave`.

**Small mismatch against `scaled_dot_product_attention`.** Differences around `1e-7` are expected — the fused kernel accumulates in a different order — and the script's `1e-5` tolerance absorbs them. Anything at `1e-5` or above is a real bug, not float noise.

# What to Say While You Type

Narration is scored. A version that works:

> "I will project to Q, K, V in one linear and split — that is one matmul instead of three. Then reshape to `(B, S, H, dh)` and transpose so heads batch. Scores are `q @ k^T` over the last two dims, scaled by `1/sqrt(dh)` to keep the logits at unit variance so softmax does not saturate. Causal mask before the softmax, so the rows still normalize. Then `probs @ v`, transpose back, contiguous because transpose leaves it strided, and the output projection."

Then, unprompted:

> "The test I actually care about is behavioral: perturb a future token and check earlier outputs do not move. Shape tests will not catch an off-by-one in the mask."

That last sentence is worth more than a clean implementation.

# Variations You Should Expect

- **"Now add a KV cache."** Module 26. Keep `past_k` and `past_v`, concatenate along the sequence axis, and note that with a cache the query length is 1 so no mask is needed during decoding.
- **"Now make it cross-attention."** Q comes from the decoder, K and V from the encoder, and there is no causal mask.
- **"Now do it without materializing the score matrix."** The FlashAttention question — tiled computation with the online softmax recurrence. The **Model Optimization Systems** track has a full module on it.
- **"What if the sequence is padded?"** Add a key-padding mask, combined with the causal mask by logical AND. Watch for fully-masked rows.
- **"Make it faster."** Fuse the QKV projection into one matmul, use `F.scaled_dot_product_attention`, and note that the real win is not materializing `(B,H,S,S)` at all.

# Further Reading

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [GQA](https://arxiv.org/abs/2305.13245) and [Fast Transformer Decoding: One Write-Head Is All You Need](https://arxiv.org/abs/1911.02150) (MQA)
- [nanoGPT `model.py`](https://github.com/karpathy/nanoGPT/blob/master/model.py) — the `CausalSelfAttention` class is the canonical compact version.
