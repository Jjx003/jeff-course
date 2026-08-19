# Where the Regime Changes

Start with the crossover, because everything else follows from it.

The attention term is $\frac{S}{12d}$ of the $6ND$ estimate. At $d = 4096$: attention is 8% of the model's FLOPs at 4k tokens, half of them at $6d \approx 25\text{k}$, and dominant beyond. Meanwhile the KV cache grows linearly and, unlike the FLOPs, it is *per concurrent sequence* — so at serving time it hits you multiplied by your batch size.

![Three panels. The first two are attention masks: a dense causal triangle, and a block-sparse pattern keeping a small budget of key blocks per query plus the local block. The third plots attention FLOPs as a percentage of the 6ND term against context length on log axes, with the dense line rising steadily past a dashed 50 percent marker while a fixed-budget selection line flattens.](/courses/ai-lab-interviews/sparse-attention.svg)

That is why the memory fix and the compute fix are different techniques, and why a serving stack usually needs both.

# Compressing the Cache

## MLA, properly

GQA shrinks the cache by making several query heads share one KV head — capacity you simply do not have any more. **Multi-head Latent Attention** instead keeps all the heads and compresses what you store.

Project each token's hidden state down to a latent $c_t \in \mathbb{R}^{512}$. Cache that. At attention time, up-project back to per-head $K$ and $V$.

Stated that way it sounds like it should cost more, not less — you have added two matmuls and you still need full-size $K$ and $V$. The trick is that **you never actually form them**:

$$q^\top k = (W_Q h)^\top (W_{UK} c) = h^\top (W_Q^\top W_{UK}) c$$

The up-projection $W_{UK}$ can be folded into $W_Q$ once, offline. The same works for $W_{UV}$ into $W_O$. So attention runs directly against the cached latent, and the "reconstruct K and V" step never happens at inference at all.

**Why RoPE has to be decoupled.** RoPE applies a position-dependent rotation to $K$. If that rotation sat between the latent and the up-projection, the product $W_Q^\top R_m W_{UK}$ would depend on position $m$ and could no longer be precomputed — the absorption trick dies. MLA's answer is to carry position in a small separate rotary key, shared across heads, concatenated to the compressed part. That is why DeepSeek-V3's cache is 512 + 64 and not just 512, and "why does MLA need a decoupled RoPE key" is the question that checks whether you actually understand it.

![Two panels. Left: cached elements per token per layer on a log scale — 32768 for MHA, 2048 for GQA-8, 256 for MQA, 576 for MLA. Right: total KV cache at batch 32 against context length for the four schemes, with a dashed line marking the aggregate memory of an eight-GPU H100 node.](/courses/ai-lab-interviews/kv-cache-schemes.svg)

**The honest caveat.** MLA is not free: it adds parameters and arithmetic, the absorbed matrices are larger, and it is substantially more work to implement than GQA. It also has to be trained in — you cannot convert a GQA checkpoint to MLA. GQA remains the right answer for most models; MLA is what you reach for when the cache is genuinely the binding constraint.

## The cheaper options

- **KV quantization** to int8 or int4. Halves or quarters the cache for a modest quality cost, works on an existing checkpoint, and composes with everything else. Usually the first thing to try.
- **Windowed layers.** Covered below — architectural, but the biggest single lever.
- **Eviction and compression at serving time** (dropping low-attention tokens). Attractive and risky: what looks droppable for the current query may be exactly what a later one needs.

# Reducing the Compute

## Sliding windows and hybrid stacks

Restrict each query to the last $w$ keys. Per-layer cache becomes constant in context rather than linear, and attention FLOPs become linear rather than quadratic.

The obvious objection is that information beyond the window is lost. It is not, quite: stacking $L$ windowed layers gives an effective receptive field of roughly $L \times w$, the same argument that makes stacked convolutions work. But the *path* is indirect, and some things genuinely need a direct look at a distant token — retrieval, in particular, degrades badly under pure windowing.

Hence **hybrid stacks**: mostly windowed layers with occasional full-attention layers. Gemma 3 runs five local to one global with a 1024-token window; GPT-OSS alternates a 128-token window with full attention. Only the global layers keep a full-length cache, so memory drops severalfold while a direct long-range path still exists every few layers.

![Four panels. The first three show attention masks: a full causal triangle, a narrow sliding-window band, and the same band with the first two columns kept attendable as sinks. The fourth plots KV cache per sequence against context length, with an all-global stack rising steeply and a five-local-to-one-global stack rising far more slowly.](/courses/ai-lab-interviews/attention-patterns.svg)

## Attention sinks

Here is the result that surprises people. Take a windowed model and evict the oldest tokens as the window slides. Quality collapses — not degrades, collapses — and it collapses specifically when the *first few* tokens leave the cache.

The reason is that softmax must sum to one. When a head has nothing it particularly wants to attend to, it still has to put its mass somewhere, and models learn to dump it on the first few positions, which are visible to every query. Those tokens are not carrying content; they are carrying *slack*. Evict them and the surplus mass redistributes onto tokens that do carry content, corrupting the output.

Two fixes: keep the first few tokens permanently (StreamingLLM's "attention sinks"), or give each head an explicit learned sink logit that participates in the softmax but has no value vector, which is what GPT-OSS does. The second is cleaner because it makes the slack explicit instead of hijacking real tokens for it.

This is a genuinely good thing to be able to explain, because it follows from softmax's normalization — a first-principles argument, not a memorized fact.

## Trained-in sparsity

Sliding windows are a fixed pattern. The natural generalization is to *choose* which keys to attend to: compress the sequence into block summaries, select the top blocks per query, and always include the local block. NSA and MoBA are the two well-known instances.

The important design point, and the reason these are architectures rather than inference tricks: sparsity has to be **trained in**. Bolting a sparse pattern onto a densely-trained checkpoint at inference time reliably underperforms, because the model's attention distributions were shaped by having everything available. Both of those designs are also explicitly built to be *hardware-efficient* — a sparse pattern that a kernel cannot execute in coalesced blocks saves FLOPs you were never bandwidth-limited on anyway, which is the trap most academic sparse-attention work fell into.

# Making Position Generalize

A model trained at 4k does not work at 128k. The failure is not subtle — it degenerates.

**RoPE base scaling.** The rotation frequency for pair $i$ is $\theta_i = b^{-2i/d_h}$. Raising the base $b$ stretches every wavelength, so position differences the model has seen stay in a familiar range. Llama 3 pretrains with $b = 500{,}000$ rather than the original 10,000 for exactly this reason.

**Post-hoc extension.** For a checkpoint you already have: position interpolation (squash positions into the trained range), NTK-aware scaling (raise the base instead, so high-frequency pairs are disturbed less), and YaRN (interpolate the low-frequency pairs, leave the high-frequency ones alone, and correct the attention temperature). YaRN is the strongest of these and needs a short fine-tune.

**The current practice** is neither of those alone: pretrain with a large base, then run a dedicated long-context training phase on genuinely long documents. Post-hoc tricks stretch what a model already learned; a training phase teaches it to use the distance. If asked "how do labs get long context", the answer that lands is "they train for it, and the interpolation tricks are for checkpoints you cannot retrain."

## The last catch: context length is not context *use*

A model advertising 1M tokens may retrieve well and reason across those tokens badly. Needle-in-a-haystack is nearly saturated and tests only retrieval; benchmarks that require combining several distant facts show much earlier degradation. If someone quotes you a context length, the follow-up worth asking is what the model can actually *do* at that length.
