## Attention math, in detail

If problem.md was the intuition, theory.md is the calculator.

### Scaled dot-product attention

Given a sequence of $L$ vectors stacked into $\mathbf{X} \in \mathbb{R}^{L \times d}$, scaled dot-product attention is

$$\text{Attention}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\!\left(\frac{\mathbf{Q}\mathbf{K}^\top}{\sqrt{d_k}}\right) \mathbf{V}$$

where $\mathbf{Q} = \mathbf{X}\mathbf{W}^Q$, $\mathbf{K} = \mathbf{X}\mathbf{W}^K$, $\mathbf{V} = \mathbf{X}\mathbf{W}^V$ with learned weight matrices $\mathbf{W}^Q, \mathbf{W}^K \in \mathbb{R}^{d \times d_k}$ and $\mathbf{W}^V \in \mathbb{R}^{d \times d_v}$.

The softmax operates row-wise on the $L \times L$ score matrix
$\mathbf{S} = \mathbf{Q}\mathbf{K}^\top / \sqrt{d_k}$. Each row $i$
becomes a probability distribution over the $L$ source positions —
the attention weights — and the output at position $i$ is the
$\mathbf{V}$-weighted sum of those positions.

### Why divide by $\sqrt{d_k}$?

If $\mathbf{q}, \mathbf{k}$ have entries roughly $\mathcal{N}(0, 1)$,
their inner product has variance $d_k$ — large $d_k$ pushes the
softmax into saturation, where one entry becomes nearly 1 and
gradients vanish. Dividing by $\sqrt{d_k}$ keeps the score variance
roughly $1$ regardless of dimension. This is the only "weird"
constant in the formula and exists to make optimisation work.

### Multi-head, formally

For $h$ heads with per-head dimension $d_k = d_v = d / h$:

$$\text{head}_i = \text{Attention}(\mathbf{X}\mathbf{W}_i^Q, \mathbf{X}\mathbf{W}_i^K, \mathbf{X}\mathbf{W}_i^V)$$

$$\text{MultiHead}(\mathbf{X}) = \text{Concat}(\text{head}_1, \dots, \text{head}_h) \mathbf{W}^O$$

with $\mathbf{W}^O \in \mathbb{R}^{d \times d}$ projecting the
concatenated heads back to the model dimension.

Total parameters of the attention block: roughly $4 d^2$ (one for each
of $\mathbf{W}^Q, \mathbf{W}^K, \mathbf{W}^V, \mathbf{W}^O$). For
ESM-2 650M with $d = 1280$ and 33 layers, that's $4 \times 1280^2 \times 33 \approx 216\text{M}$ params from attention alone.

### Computational cost

Self-attention's compute and memory both scale as $O(L^2 d)$:

- Score matrix is $L \times L$: $O(L^2 d_k)$ work to build, $O(L^2)$
  to softmax, $O(L^2 d_v)$ to apply.
- Plus $O(L d^2)$ for the linear projections.

For a 1000-residue protein with $d = 1280$, building the score matrices
costs $\approx L^2 d = 1.3\text{B}$ multiply-adds per layer (summed across
all heads, since the per-head cost $L^2 d_k$ times $h$ heads recovers
$L^2 d$) — fast on a GPU but quadratic in $L$. This is why long-protein
inference is hard, and why techniques like FlashAttention and chunked
processing exist.

## The "compressed database" intuition, mathematically

Why does the compressed-database framing actually work? The key
observation is that gradient descent on a masked-language-model loss
forces the model to memorise statistical regularities of the training
distribution.

Here's a worked example. Suppose during pretraining the model sees
millions of globin sequences. Many of them have a conserved `WGK`
motif near position 50. When the model encounters a sequence with a
`<MASK>` at position 51 right after `WG`, an internal pattern emerges:

- Some attention head has learned to attend strongly to the previous
  two positions when they are `WG`.
- Some FFN neurons activate strongly when the previous-2 attention
  output looks like `WG`.
- Those FFN neurons project to logits that put high probability on `K`.

The model has *implicitly* compressed the pattern "after `WG` comes
`K`" into its weights. At inference, when shown a new sequence with
`WG?` at the relevant position, it retrieves that pattern through
attention + FFN and produces a high-probability `K` prediction.

This is exactly the BLOSUM62 analogy *but learned, contextual, and
combinatorially richer*: instead of a $20 \times 20$ table that says
"K is similar to R" globally, the transformer has $\text{many billions}$
of learned associations that say "K is the right completion when
preceded by W and G in a globin-like context".

## Attention vs convolution

A useful contrast for those coming from CNN backgrounds:

| Property | 1D Convolution | Self-Attention |
|---|---|---|
| Receptive field per layer | Fixed (kernel size) | Full sequence |
| Long-range dependencies | Need many layers | Single layer |
| Position dependence | Translation-equivariant | Position-aware via PE / RoPE |
| Compute per token | $O(d k)$ per layer | $O(L d)$ per layer |
| Memory per layer | $O(L d)$ | $O(L^2 + L d)$ |

For proteins, where long-range residue contacts dominate the fold
problem, attention's "single-layer global reach" is the killer
feature. CNN-based protein models (RaptorX, DeepCNF) plateaued well
before transformers came along.

## Encoder vs decoder

This module's analogy is specifically about **encoder** transformers
— the BERT / ESM-2 / ESMFold lineage. They use *bidirectional*
self-attention: every position attends to every other position, both
left and right.

**Decoder** transformers (GPT, the LLaMA family, the autoregressive
coding models) use *causal* self-attention with a triangular mask:
position $i$ attends only to positions $\le i$. This is what enables
left-to-right text generation but makes them less natural fits for
the bidirectional "fill in the blank" tasks of protein modelling.

ESM-2 is encoder-only and trained with masked-language-modelling. ESM3
(module 14) re-introduces a multimodal generative twist, but at its
core it's still primarily encoder-style.

## Layer-by-layer pattern refinement

A common observation about deep transformers: information sharpens
and abstracts as you ascend the stack.

- **Early layers (1-6)** look mostly at near-neighbour patterns —
  amino-acid identity, immediate sequence context, basic
  hydropathy / charge categorisation.
- **Middle layers (7-20)** integrate longer-range information —
  secondary-structure assignment, inferred MSA-like signal, motif
  detection.
- **Late layers (21+)** carry abstract, task-aligned features —
  fold class, function category, contact-map predictions.

This isn't a hard partition; it's a smooth gradient. A neat empirical
demo (Rao et al, Vig et al): you can attach a contact-map prediction
head to *any* layer and find that mid-to-late layers give the best
contact predictions, with a bump near the very last layers.

For module 12 we'll extract embeddings from a specific layer of ESM-2
and see them as the "compressed-database lookup" output. The choice of
which layer to extract from is essentially the question of which
abstraction level you want.

## Reading the architecture diagram of any transformer paper

Once you have the fuzzy-matching mental model, the architecture
diagrams in transformer papers (AlphaFold2's Evoformer, ESM-3's
multimodal block, etc.) become much more readable. The recipe:

1. Identify the queries, keys, and values. Often there are *several*
   parallel sets — row-wise vs column-wise attention, sequence vs
   pair representation, etc.
2. Identify the per-position transformations (FFNs, gating).
3. Identify the residual connections that let the representation
   refine without losing signal.

Modules 15 and 16 do exactly this for AlphaFold2's Evoformer — the
core of the architecture is "row attention + column attention + outer
product mean", and each piece is just a specialised version of the
fuzzy-matching loop you now understand.
