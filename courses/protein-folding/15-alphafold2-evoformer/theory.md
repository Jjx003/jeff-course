<p align="center">
  <img src="/images/protein-folding/evoformer.svg" alt="Evoformer Block Architecture" />
</p>

## Gated attention, in detail

AlphaFold2 uses gated attention everywhere. The gate is a learned,
input-dependent multiplicative mask:

$$\mathbf{g} = \sigma(\mathbf{W}^G \mathbf{x})$$

$$\text{output} = \mathbf{g} \odot \text{Attention}(\mathbf{x})$$

Why gates help, mechanically:

- **Selective output flow.** Standard attention always passes its
  output through; gating lets the model output near-zero for
  positions / channels where the attention isn't useful, without
  fighting the residual stream.
- **Better optimisation.** Empirically, gated attention converges
  faster and to lower loss. The exact reason is debated, but a common
  hypothesis is that the multiplicative interaction between gate and
  attention output makes loss landscapes smoother.
- **Compatibility with deep stacks.** AlphaFold2 has 48 Evoformer
  blocks. Without gating, the residual stream tends to accumulate
  uncontrolled magnitude across so many layers; gates provide an
  attenuator.

## Pair bias, in detail

The pair-derived row attention bias deserves a closer look. From the
formula:

$$b_{ij} = \mathbf{w}_b^\top \mathbf{z}_{ij}$$

with $\mathbf{w}_b \in \mathbb{R}^{c_z}$ a learned vector. So each
attention head computes its own scalar bias from the pair
representation. There are typically 8 heads, so 8 different
projections of $\mathbf{z}_{ij}$.

What does the bias *do*? It modulates the attention scores before
softmax:

$$\alpha_{k, ij} \propto \exp\!\left(\frac{\mathbf{q}_{k, i}^\top \mathbf{k}_{k, j}}{\sqrt{c_h}} + b_{ij}\right)$$

A large positive $b_{ij}$ pushes attention from $i$ to $j$ up across
all sequences in the MSA. Conceptually:

> "The pair representation has decided $i$ and $j$ are spatially
> close. Make sure each row's representation at $i$ is informed by
> what's at $j$."

A large negative bias pushes attention down — "these positions
shouldn't share information".

This is the cleanest example of **structural priors influencing
sequence features** in the architecture. Without pair bias, row
attention would be sequence-context-only; with it, row attention is
structure-aware.

## Why the pair representation has its own attention

Module 15 mentions that the pair representation also goes through
attention operations (called "triangular attention" in the AlphaFold2
paper). We didn't unpack them in problem.md to keep the focus on the
MSA side. A short summary:

- **Triangular multiplicative update.** For each pair $(i, j)$,
  combine information from all triplets $(i, j, k)$ via outer
  products of $\mathbf{z}_{ik}$ and $\mathbf{z}_{kj}$. Encodes
  triangle-inequality-style consistency: if $i$ is close to $k$ and
  $k$ is close to $j$, then $i$ is at most a fixed distance from $j$.
- **Triangular attention.** Self-attention over either the row index
  ($i$) or the column index ($j$) of the pair representation, with
  another bias term that ties the two indices together.

These four operations (two multiplicative, two attention) are the
"pair-side" half of the Evoformer block. The MSA side and pair side
exchange information once per block via the outer product mean
(module 16) and the pair bias.

## Tensor shapes — concrete numbers

For a typical AlphaFold2 forward pass on a 200-residue protein with a
deep MSA:

- $\mathbf{m}$: $(512, 200, 256)$. ~26 M scalars.
- $\mathbf{z}$: $(200, 200, 128)$. ~5 M scalars.

Memory of activations across 48 Evoformer blocks (with
gradient-checkpointing): ~10-20 GB.

Compute per Evoformer block:

- Row attention (with pair bias): $O(S L^2 c_h h) = 512 \times 200^2 \times 32 \times 8 \approx 5 \cdot 10^9$ FLOPs.
- Column attention: $O(L S^2 c_h h) = 200 \times 512^2 \times 32 \times 8 \approx 1.3 \cdot 10^{10}$ FLOPs.
- MSA transition: $O(S L c_m \times 4 c_m) \approx 5 \cdot 10^7$ FLOPs.
- Outer product mean (module 16): $O(S L^2 c'^2) \approx 10^8$.
- Triangle updates: $O(L^3 c_z)$ — this can dominate for long sequences.

Total per block: ~10-20 GFLOPs. Across 48 blocks: ~500 GFLOPs.

Forward pass time on an A100: ~1-2 minutes for a 200-residue protein.
Most of the time goes to MSA search and recycling iterations
(Evoformer is run multiple times, feeding outputs back as inputs).

## Why $S = 512$?

AlphaFold2 trims its MSA to a maximum of 512 sequences (sub-sampled
from a much deeper alignment) for tractability. The $O(S^2)$ scaling
of column attention is the main reason — at $S = 1024$ it's 4× slower
in column attention alone.

Empirically, accuracy plateaus once you have ~1000 sequences in the
MSA. After 512 the marginal information from additional homologs is
small and not worth the compute.

## Recycling

A subtle but important detail: AlphaFold2 runs the Evoformer (and
structure module) **three times** in sequence, feeding the output of
each iteration back as part of the input to the next. This is called
**recycling** in the paper.

Why? The first pass produces a rough fold; the second and third
refine it. Recycling is the architectural realisation of the
intuition that protein folding is iterative — fix some of the
backbone first, then use that to predict more, then refine.

ESMFold drops recycling (single forward pass) for speed but also
ends up slightly less accurate as a result.

## What the structure module does

Once the Evoformer outputs $\mathbf{s}$ (single representation,
length $L$) and $\mathbf{z}$ (pair representation, $L \times L$), the
**structure module** turns them into 3-D coordinates.

The mechanism is:

1. Initialise each residue at the origin with identity rotation.
2. Predict per-residue affine transforms (translation + quaternion
   rotation) from $\mathbf{s}$ and $\mathbf{z}$.
3. Apply them iteratively (8 layers of "IPA" — Invariant Point
   Attention — interleaved with backbone updates).
4. Out comes a per-residue affine giving the position and orientation
   of each backbone frame.

This is its own complex topic and deserves a separate module — we
won't cover it in detail here. The important takeaway is that the
Evoformer's job is to produce the **right pair representation**;
the structure module's job is to read off coordinates from it.

## Comparing to module 10's framing

The compressed-database analogy from module 10 still applies, but
extended:

- **The compressed database** consists of patterns about both
  *single sequences* (in the MSA representation channels) and
  *residue pairs* (in the pair representation).
- **The query** is the input MSA + sequence, processed iteratively
  through 48 layers of attention.
- **The retrieved match** is the pair representation, which encodes
  pairwise residue information that maps directly to a 3-D fold.

Compared to a sequence-only PLM:

- AlphaFold2 has the *explicit* MSA at inference time → it can
  exploit MSA-derived signal directly.
- AlphaFold2 has *explicit* pair representation → contact / distance
  prediction is built into the architecture, not something inferred.
- AlphaFold2 is *trained on (sequence, structure) pairs from the
  PDB* → its loss has a direct structural component, unlike
  ESM-2's pure-sequence MLM.

These three architectural commitments are what made AlphaFold2 work
in 2020. ESMFold (module 17) shows that you can give them all up
*if* you scale the language model enough — and lose only a little
accuracy in exchange for huge speed and removal of the MSA dependency.
