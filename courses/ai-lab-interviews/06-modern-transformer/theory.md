# Attention

## Scaled dot-product attention

$$\mathrm{Attention}(Q,K,V) = \mathrm{softmax}\!\left(\frac{QK^{\top}}{\sqrt{d_k}} + M\right)V$$

Shapes, which you should be able to recite:

| Tensor | Shape |
|---|---|
| Input $x$ | $(B, S, d)$ |
| $Q, K, V$ after projection | $(B, S, d)$ |
| After head reshape | $(B, H, S, d_h)$ where $d_h = d/H$ |
| Scores $QK^{\top}$ | $(B, H, S, S)$ |
| Output before merge | $(B, H, S, d_h)$ |
| Output after merge and $W_O$ | $(B, S, d)$ |

![Three panels. Left: standard deviation of attention logits against head dimension, growing as the square root of head dimension without scaling and staying flat with it. Middle: mean maximum softmax probability, approaching 1.0 without scaling. Right: the summed softmax Jacobian, collapsing toward zero without scaling.](/courses/ai-lab-interviews/attn-softmax-scaling.svg)

## Why divide by $\sqrt{d_k}$

If the entries of $q$ and $k$ are independent with mean 0 and variance 1, then $q\cdot k = \sum_{i=1}^{d_k} q_i k_i$ has variance $d_k$ and standard deviation $\sqrt{d_k}$. Without the scaling, the logits entering softmax grow with head dimension. Large-magnitude logits make softmax saturate — one entry near 1, the rest near 0 — and a saturated softmax has a vanishing gradient, since the Jacobian entries are $p_j(1-p_j)$ and $-p_ip_j$.

Dividing by $\sqrt{d_k}$ returns the logits to unit variance regardless of head dimension. It is a variance-control argument, and stating it that way is the answer that lands.

## The causal mask

![Three panels. Left: the lower-triangular causal mask. Middle: the resulting attention weights. Right: row sums of the attention weights, at 1.0 when masking before the softmax and far below 1.0 for early positions when masking after.](/courses/ai-lab-interviews/attn-causal-mask.svg)

Set every position where the key index exceeds the query index to $-\infty$ **before** the softmax:

```python
mask = torch.ones(S, S, dtype=torch.bool).tril()
scores = scores.masked_fill(~mask, float("-inf"))
probs = scores.softmax(dim=-1)
```

**Why before and not after.** Zeroing probabilities after the softmax would leave the remaining rows unnormalized — they would no longer sum to 1, and the output would be a shrunken convex combination whose scale depends on position. Masking before means the softmax normalizes over exactly the allowed set.

**Why $-\infty$ and not a large negative number.** In fp32 and bf16 a sentinel like `-1e9` actually does give exactly zero probability after the max subtraction — bf16 shares fp32's exponent range, so it is comfortably representable. The real hazards are: **fp16**, whose maximum is 65504, so `-1e9` becomes `-inf` on the cast anyway or overflows unpredictably; and any pipeline that *adds* a second bias or mask afterwards, which can pull a finite sentinel back into a range where it contributes. `float("-inf")` is unambiguous under all three. The one wrinkle: a row that is entirely masked yields `nan`, which is why implementations that pad on the left need care.

## MHA, MQA, GQA

The problem GQA solves is not compute, it is **memory bandwidth during decoding**.

At every generated token, the model reads the entire KV cache from HBM. Decoding is memory-bound, not compute-bound, so the size of the cache directly sets the token rate.

| Variant | KV heads | Cache size | Quality |
|---|---|---|---|
| MHA | $H$ | $1\times$ | baseline |
| MQA | 1 | $1/H$ | measurable degradation, training instability reported |
| GQA | $G$, typically 4–8 | $G/H$ | essentially baseline |

GQA partitions the $H$ query heads into $G$ groups, each sharing one K head and one V head. Llama 2 70B uses 64 query heads and 8 KV heads — an 8x cache reduction. In code, the only change is a `repeat_interleave` (or an expanded view) of K and V before the score matmul.

**The interview follow-up:** "Why not just use MQA if the cache is the problem?" Because collapsing to a single KV head loses too much representational diversity and destabilizes training at scale; GQA was introduced precisely as the interpolation that keeps almost all the quality with almost all the savings.

# Positional Information

You should be able to list all four families and give a trade-off for each.

## 1. Sinusoidal absolute (2017)

Fixed sines and cosines at geometrically spaced frequencies, added to the embedding. No parameters, and in principle extrapolates. In practice models do not learn to use it beyond the training length.

## 2. Learned absolute (GPT-2, BERT)

A trainable table of shape $(S_{max}, d)$, added to the embedding. Simple and effective — and hard-capped at $S_{max}$. There is no defined behavior past the end of the table, which is the reason GPT-2 cannot exceed 1024 tokens.

## 3. Relative bias (T5, ALiBi)

Add a bias to the attention scores that depends on the distance $i - j$. T5 learns a bucketed bias; ALiBi uses a fixed linear penalty $-m \cdot |i-j|$ with a per-head slope $m$. ALiBi extrapolates remarkably well and costs nothing to compute, but it bakes in a strong recency prior.

## 4. Rotary (RoPE) — the current default

![Three panels. Left: cosine of the rotation angle against token position for five channel pairs, showing wavelengths from 6 to nearly 20000 tokens. Middle: wavelength against channel pair index on a log scale, a straight line. Right: the dot product of a rotated query and key against relative offset, with three different absolute base positions falling exactly on top of one another.](/courses/ai-lab-interviews/rope-frequencies.svg)

Rather than adding anything, RoPE **rotates** Q and K by an angle proportional to position, in 2-D subspaces of the head dimension. For a pair of channels $(2i, 2i+1)$ at position $m$:

$$\theta_i = \frac{1}{10000^{2i/d_h}}, \qquad \begin{pmatrix} q'_{2i} \\ q'_{2i+1}\end{pmatrix} = \begin{pmatrix}\cos m\theta_i & -\sin m\theta_i \\ \sin m\theta_i & \cos m\theta_i\end{pmatrix}\begin{pmatrix} q_{2i} \\ q_{2i+1}\end{pmatrix}$$

**The key property.** Because a rotation by $m$ followed by the inverse rotation by $n$ is a rotation by $m-n$, the dot product $q_m' \cdot k_n'$ depends only on the *relative* offset $m-n$. Absolute position enters the computation, but only relative position survives into the attention scores.

**Why this is better in practice:**

- Relative by construction, with no extra parameters and no addition to the residual stream.
- Applied to Q and K only, never to V — position should affect *which* tokens you attend to, not *what* is retrieved from them.
- Extends cleanly: rescaling the base (NTK-aware scaling) or the position index (linear interpolation) buys longer context with modest continued pretraining. This is how nearly every long-context extension in the wild is done, and it is a very common follow-up question.

**The gotcha worth knowing:** the "interleaved" convention pairs channels $(0,1), (2,3), \dots$ — this is what Meta's reference `llama/model.py` does, via complex arithmetic over adjacent pairs. The "split-half" convention pairs $i$ with $i + d_h/2$, and is what HuggingFace `transformers` and GPT-NeoX use, which is precisely why the HF conversion script permutes the Q and K weights. Both are valid rotations, but a checkpoint trained with one and served with the other produces fluent-sounding garbage. This is a real production bug and an excellent thing to mention.

# Normalization

## LayerNorm

$$\mathrm{LN}(x) = \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}}\odot\gamma + \beta$$

normalizing over the feature dimension, per token. Note this is per-token — unlike BatchNorm, it has no dependence on other examples, which is what makes it usable with variable batch sizes and during autoregressive decoding.

## RMSNorm

$$\mathrm{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{d}\sum_i x_i^2 + \epsilon}}\odot\gamma$$

Drops the mean subtraction and the bias. The empirical finding is that re-centering contributes essentially nothing — the benefit is re-scaling — so you save a reduction pass and $d$ parameters per norm. At scale that is a real fraction of the memory-bandwidth cost of a layer.

**The implementation detail interviewers probe:** compute the norm in float32 even when the model runs in bf16. Summing squares of bf16 values across thousands of channels loses far too much precision. Every serious implementation upcasts inside the norm and downcasts on the way out.

## Pre-norm versus post-norm

**Post-norm** (2017): `x = Norm(x + Sublayer(x))`. Every residual passes through a normalization, so the gradient path from the loss to layer 1 is squeezed at every step. Deep post-norm stacks need careful learning-rate warmup and still diverge.

**Pre-norm** (everything modern): `x = x + Sublayer(Norm(x))`. The residual stream is a clean additive highway from input to output; gradients reach early layers undiminished. Pre-norm models train stably at 100+ layers.

The cost is that the residual stream's magnitude grows with depth, which is why a **final norm** before the output head is mandatory in pre-norm architectures — forget it and the logits are badly scaled. Omitting the final norm is one of the classic seeded bugs in a debug-the-transformer interview.

# The Feed-Forward Network

Standard: $\mathrm{FFN}(x) = W_2\,\mathrm{ReLU}(W_1x)$ with hidden size $4d$, giving $8d^2$ parameters.

SwiGLU: $\mathrm{FFN}(x) = W_3(\mathrm{Swish}(W_1x)\odot W_2x)$ with hidden size $\tfrac{8}{3}d$, giving $3 \cdot d \cdot \tfrac{8}{3}d = 8d^2$ parameters — deliberately the same.

The FFN is where most of a transformer's parameters live, and there is good evidence it is where most factual knowledge is stored. It is also the component MoE replaces: swap one FFN for $N$ experts plus a router, activate the top-$k$, and parameters grow while per-token FLOPs do not.

# Parameter Accounting

Per layer, no biases:

- Attention: $4d^2$ — that is $W_Q, W_K, W_V, W_O$. With GQA, $W_K$ and $W_V$ shrink by $G/H$.
- FFN: $8d^2$
- **Total: $12d^2$ per layer**

Plus embeddings: $Vd$, and the output head, another $Vd$ unless tied.

$$N \approx 12Ld^2 + Vd$$

![Two panels. Left: stacked parameter counts for GPT-2 small, GPT-2 XL, Llama-2 7B and Llama-2 70B, split into attention, FFN and embeddings. Right: embeddings as a percentage of total parameters, 31% for GPT-2 small falling to under 1% for Llama-2 70B.](/courses/ai-lab-interviews/params-breakdown.svg)

**Worked example, Llama-2-7B:** $L=32$, $d=4096$, $V=32000$.

$12 \times 32 \times 4096^2 = 6.44$B, plus $32000 \times 4096 = 0.13$B embeddings. About 6.6B, against a real count of 6.74B. The 0.16B gap is almost entirely the **untied output head** — Llama-2 does not tie, so it pays $Vd$ twice (0.13B) — plus the rounded SwiGLU hidden size of 11008 rather than 10923 (0.03B). Note 7B uses full MHA (32 query heads, 32 KV heads); GQA appears only in the 34B and 70B, and it would *reduce* the count, not raise it. Being able to do this estimate live, out loud, and land within 5% is a strong signal.

# After 2023: The Deltas Interviewers Now Expect

The Llama-style stack above is still the reference answer, but several post-2023 changes have become standard interview material in their own right. Know them at one level of depth: what each one is, what it replaces, and why.

## Multi-head Latent Attention (MLA)

GQA shrinks the KV cache by *sharing* heads. MLA — introduced in DeepSeek-V2 and carried through V3 and R1 — shrinks it by **low-rank compression** instead: project each token's K and V into a single shared latent vector, cache only that latent plus a small "decoupled" RoPE key, and reconstruct per-head K and V with up-projections. Two details make it work, and both are good interview material:

- **The up-projections never run at inference.** Because attention is bilinear, the K up-projection can be absorbed into $W_Q$ and the V up-projection into $W_O$, so attention operates against the cached latent directly and full-size K and V are never materialized.
- **RoPE has to be decoupled.** A position-dependent rotation sitting between the latent and the up-projection would break that absorption trick, so MLA carries position in a small separate rotary key shared across heads.

The numbers, per token per layer for DeepSeek-V3: a 512-dim latent plus a 64-dim RoPE key = 576 cached elements, versus $2 \times 8 \times 128 = 2048$ for a GQA model with 8 KV heads at head dim 128, and $2 \times 128 \times 128 = 32{,}768$ for its 128 query heads under full MHA. Unlike MQA and GQA, which buy cache with a little quality, DeepSeek reports MLA at or above MHA quality. "GQA versus MLA" is now a standard follow-up to any KV-cache discussion.

![Two panels. Left: cached elements per token per layer on a log scale, 32768 for MHA, 2048 for GQA-8, 256 for MQA and 576 for MLA. Right: total KV cache at batch 32 against context length for the four schemes, with a dashed line at the aggregate memory of an eight-GPU H100 node.](/courses/ai-lab-interviews/kv-cache-schemes.svg)

## QK-norm

Apply an RMSNorm to the queries and keys (over the head dimension) after projection, before RoPE and the score matmul. It bounds the attention logits, which shuts off a specific large-scale failure: logits grow during training, softmax saturates, and the loss spikes. Introduced for ViT-22B, now standard in Gemma 3, Qwen3, and OLMo 2. If asked what to do about attention-logit blowups, QK-norm is the current answer; Gemma 2's logit soft-capping was the interim one.

## Hybrid local/global attention

Rather than every layer paying full-context attention, current models interleave **sliding-window layers** with occasional full-attention layers — Gemma 3 runs five local layers (1024-token window) per global layer; GPT-OSS alternates a 128-token window with full attention. Only the global layers keep a full-length KV cache, so long-context memory drops severalfold with little quality cost. This is often paired with **attention sinks**: models dump surplus attention mass on the first tokens, so those are kept permanently attendable (or replaced by a learned per-head sink logit, as in GPT-OSS) — evict them from the cache and quality collapses.

![Four panels. The first three show which keys a query may attend to: a full causal triangle, a narrow sliding-window band, and the same band with the first two columns kept attendable as sinks. The fourth plots KV cache per sequence against context length, with an all-global stack rising steeply and a five-local-to-one-global stack rising far more slowly.](/courses/ai-lab-interviews/attention-patterns.svg)

## Long context by default

The train-at-4k-then-extend era is over. Current models pretrain with a much larger RoPE base — Llama 3 uses 500,000 — and add a staged long-context phase, shipping 128k+ natively. Interpolation, NTK-aware base scaling, and YaRN remain the right answer for stretching an *existing* checkpoint, but "how do labs get long context" is now answered with base scaling plus long-context training, not post-hoc tricks alone.

# Weight Tying

Share the embedding matrix with the output projection: $W_{out} = W_{emb}^{\top}$. Saves $Vd$ parameters.

- At $d=768, V=50257$: 38M of a 124M-parameter model. Enormous.
- At $d=8192, V=128000$: 1B of a 70B model. Marginal.

So it matters most at small scale, which is why GPT-2 ties and several large modern models do not. The backward-pass subtlety is worth mentioning: a tied matrix receives gradient from *both* the embedding lookup and the output projection, and those gradients sum. That is the branch-sum rule biting in a real architecture.
