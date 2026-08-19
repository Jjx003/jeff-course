# Rapid-Fire: Long Context

**"How do you handle long context?"**
> Separate the three problems first: attention compute is $O(S^2)$, KV cache is $O(S)$ per sequence, and positional generalization just breaks. They have different fixes. Answering "FlashAttention" is wrong — it removed the $O(S^2)$ *memory* of the score matrix, not the FLOPs and not the cache.

**"Which one actually binds?"**
> At serving time, the cache — because it is multiplied by concurrent sequences while the FLOPs are not. Attention compute becomes half the model's FLOPs around $6d$ tokens, about 25k at $d = 4096$.

**"Explain MLA."**
> Compress K and V into one latent per token, cache that, and up-project per head. The up-projections fold into $W_Q$ and $W_O$ because attention is bilinear, so at inference you attend against the latent directly and never materialize K and V.

**"Why does MLA need a decoupled RoPE key?"**
> A position-dependent rotation between the latent and the up-projection would make the folded matrix depend on position, so it could not be precomputed. MLA carries position in a small separate rotary key shared across heads. That is why DeepSeek-V3 caches 512 + 64.

**"MLA versus GQA?"**
> GQA ties heads together and gives up a little quality for it; MLA keeps all heads and compresses instead, reportedly at or above MHA quality. MLA costs more parameters, more arithmetic, and much more implementation effort, and it must be trained in. GQA is still right for most models.

**"Sliding windows throw away distant information. Why do they work?"**
> Stacking $L$ windowed layers gives an effective receptive field around $L \times w$. The path is indirect, though, and retrieval suffers — which is why real models are hybrids with a full-attention layer every few blocks.

**"What is an attention sink?"**
> Softmax has to sum to one, so a head with nothing to attend to dumps its mass on the first few positions, which every query can see. Those tokens carry slack, not content. Evict them and the mass redistributes onto real tokens and output collapses. Fix by pinning the first tokens, or by giving each head a learned sink logit with no value vector.

**"Why not just apply a sparse pattern at inference?"**
> Because attention distributions were shaped by having everything available. Sparsity has to be trained in — that is the point of NSA and MoBA — and the pattern has to be block-structured enough for a kernel to run it efficiently, or you save FLOPs you were not limited by.

**"How do you extend a model's context?"**
> Post-hoc: position interpolation, NTK-aware base scaling, YaRN (best of the three, needs a short fine-tune). But current models are pretrained with a large RoPE base — Llama 3 uses 500,000 — plus a dedicated long-context phase. Labs train for it; interpolation is for checkpoints you cannot retrain.

**"A model claims 1M context. What do you ask?"**
> What it can do at that length. Needle-in-a-haystack is saturated and only tests retrieval; tasks requiring several distant facts to be combined degrade far earlier.

## Going deeper

- [FlashAttention](https://arxiv.org/abs/2205.14135) — read it for what it does and does not solve.
- [StreamingLLM](https://arxiv.org/abs/2309.17453) — the attention-sink result, and a clean example of a surprising empirical finding with a one-line explanation.
- [YaRN](https://arxiv.org/abs/2309.00071) — the best-understood post-hoc context extension method.
- [DeepSeek-V2](https://arxiv.org/abs/2405.04434) — where MLA is introduced, including the decoupled RoPE derivation.
- [Native Sparse Attention](https://arxiv.org/abs/2502.11089) — trained-in, hardware-aligned sparsity; the argument for why both properties are necessary.
