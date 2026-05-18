## Recycling, in detail

A subtle but powerful component of AlphaFold2: **recycling**. The
Evoformer + structure module run *three times* per inference, with
each iteration's outputs fed back as part of the inputs to the next.

The recycling inputs are:

- The previous iteration's pair representation $\mathbf{z}^{(t-1)}$.
- The previous iteration's first-row MSA representation
  $\mathbf{m}^{(t-1)}_{1, :, :}$ (only the query row).
- A discretised distance map computed from the previous iteration's
  predicted CA positions.

These are added to the fresh inputs at the very start of the next
iteration. Conceptually:

> Run the network. Get a rough structure. Use it as a structural prior
> for a second pass. Get a better structure. Iterate.

Recycling adds about 3× compute but ~10-15 GDT_TS points of accuracy.
ESMFold (next module) drops recycling for speed and pays the cost in
accuracy.

## Why $c' = 32$?

The OPM's intermediate channel dimension is small (32) compared to
$c_m = 256$ and $c_z = 128$. Why?

- **Compute scaling.** The intermediate tensor is
  $(L, L, c'^2)$. For $c' = 32$, $c'^2 = 1024$. For $c' = 64$,
  $c'^2 = 4096$ — 4× more memory.
- **Signal vs noise.** The outer-product-mean's purpose is to
  detect co-variation patterns; you need *enough* dimensions to
  encode multiple patterns but not so many that random noise
  dominates the average. 32 is empirically a good balance.
- **Implicit regularisation.** Forcing the model to compress the MSA
  representation through a 32-dim bottleneck before doing the outer
  product encourages the projections to encode "co-variation-relevant"
  features rather than memorising the full MSA channel.

These are all empirical justifications; there's no first-principles
derivation of $c' = 32$ in the paper.

## OPM as a learnable mutual-information statistic

Recall mutual information for two discrete random variables $X, Y$:

$$I(X; Y) = \sum_{x, y} p(x, y) \log \frac{p(x, y)}{p(x) p(y)}$$

Mutual information is high when $X$ and $Y$ are dependent. For MSA
columns, treating each column's residue as a random variable and
computing $I(X_i; X_j)$ across the MSA is the simplest co-evolution
detector.

Compare to OPM. OPM's per-pair output is

$$\Delta \mathbf{z}_{ij} = \mathbf{W}^O \,\text{flatten}\!\left( \mathbb{E}_k \left[ \mathbf{a}_{k,i} \otimes \mathbf{b}_{k,j} \right] \right)$$

The expectation is the *empirical* expectation over the MSA. The
outer product captures all second-order joint statistics of
$\mathbf{a}_{k,i}, \mathbf{b}_{k,j}$. The linear projection
$\mathbf{W}^O$ extracts a learned summary.

Mutual information is one specific scalar summary of the joint
distribution; OPM is a *learned* multi-channel summary. So OPM
strictly generalises MI.

In practice, the network learns projections such that the OPM output
correlates with mutual information at non-zero values, while also
encoding additional structural priors (e.g. helix vs sheet, distance
between residues). End-to-end training tells the network which
combinations of joint statistics are most useful for downstream
structure prediction.

## DCA: the prior art

Before AlphaFold2, the dominant explicit co-evolution method was
**Direct Coupling Analysis (DCA)** (Morcos et al, 2011; Marks et al,
2011). DCA models the MSA as samples from a Potts model:

$$P(X_1, \dots, X_L) = \frac{1}{Z} \exp\!\left( \sum_i h_i(X_i) + \sum_{i < j} J_{ij}(X_i, X_j) \right)$$

The $J_{ij}$ matrices are 21x21 (20 amino acids + gap) coupling
matrices. Fitting them via pseudolikelihood (PLMDCA) or mean field
(MF-DCA) recovers contact maps with reasonable accuracy. EVfold and
GREMLIN are well-known implementations.

DCA's strengths:

- Theoretically clean (proper probabilistic model).
- Interpretable per-pair.
- Works with no neural network.

DCA's weaknesses:

- Requires deep MSAs ($\ge 5L$ sequences typically) to fit cleanly.
- Single point estimate per pair — no uncertainty.
- Independent of structural prior knowledge.

OPM addresses all three weaknesses simultaneously: it's part of a
deep neural network trained end-to-end, so it benefits from
structural priors and downstream gradient feedback. It works at any
MSA depth (as small as $S = 1$, in which case OPM degenerates to a
simple bilinear function and the network leans more heavily on the
pair-attention components).

## What does the pair representation actually encode?

After 48 Evoformer blocks of MSA-pair iteration, the pair
representation $\mathbf{z}_{ij}$ is a learned 128-dim summary of
"the relationship between residues $i$ and $j$ in this protein". Linear
probes on the trained pair representation recover:

- **Distance** between residues' CA atoms (the most prominent feature).
- **Relative orientation** between backbone frames.
- **Contact identity** (yes/no within 8 Å).
- **Secondary-structure relationship** (same helix, same sheet, etc.).
- Some **functional** features (active-site distance, ligand
  proximity).

The structure module reads off coordinates from this representation
in a single (well, 8-layer iterative) pass.

## Why this architecture beat DCA + ResNet by so much

Pre-AlphaFold2 contact prediction pipelines (RaptorX, trRosetta) used
DCA features as inputs to a deep CNN that predicted contact maps,
then fed the contact predictions to a fold-from-distances solver. They
got CASP12-13 GDT_TS scores around 50.

AlphaFold2's CASP14 GDT_TS was 92.

The architectural advantages over the CNN baseline:

1. **End-to-end gradient flow** from structure loss back through both
   the CNN and the DCA-replacement (= OPM). The CNN baselines treated
   DCA as a fixed feature extractor.
2. **Iterative refinement** via Evoformer's 48 blocks + 3 recycling
   passes. CNN baselines were single-pass.
3. **Geometric structure module** that produced 3-D coordinates
   directly from the pair representation, end-to-end differentiable.
   CNN baselines used a separate 3-D fold-search (Rosetta or similar)
   downstream.

Each piece contributed; the OPM specifically replaced DCA with a
learned, expressive, gradient-friendly version.

## Implementation tips, if you ever build this

- **Don't materialise $(S, L, L, c'^2)$.** Use einsum to compute the
  per-pair mean directly:
  ```python
  delta_z = torch.einsum("ski,skj->ijij", a, b) / S
  ```
  (Schematically — the actual code goes through the flatten step.)
- **Layer-norm a and b** before outer product. AlphaFold2 does, and
  it stabilises training.
- **Drop sequence weighting** unless you're being very careful — the
  raw mean treats every sequence equally; sequence-weighted DCA
  variants exist but are tricky to backpropagate through.

## Connection to attention

A subtle observation: the OPM is *not* attention. There's no softmax,
no query-key matching, no token-to-token mixing. The output for pair
$(i, j)$ depends *only* on column $i$ and column $j$ of the MSA, not
on any other columns. The "across-sequence" mixing happens via the
mean over $S$, not via attention.

This is intentional. Attention would be much more expensive
($O(SL^2)$ scores per layer) and would also be redundant with the
Evoformer's column attention (which already mixes across sequences).
The OPM is the cheaper, complementary operation.

## Recap

- The OPM is the MSA-side bridge to the pair representation.
- It's a learned generalisation of DCA / mutual information.
- The intermediate channel $c' = 32$ keeps it tractable.
- Combined with row attention's pair-bias channel, it forms a
  bidirectional information flow between $\mathbf{m}$ and $\mathbf{z}$
  that runs 48 times per Evoformer pass.
- This explicit MSA-co-evolution machinery is what ESMFold (next
  module) gives up in exchange for speed.
