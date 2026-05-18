## Why cosine similarity?

For two non-zero vectors $\mathbf{u}, \mathbf{v} \in \mathbb{R}^d$,
cosine similarity is

$$\text{cos}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u}^\top \mathbf{v}}{\lVert \mathbf{u} \rVert_2 \lVert \mathbf{v} \rVert_2}$$

Geometrically: the cosine of the angle between the vectors. Range
$[-1, 1]$. Equals 1 when the vectors point the same direction, 0 when
orthogonal, $-1$ when antiparallel.

For PLM embeddings, cosine similarity has two practical properties:

1. **Magnitude-invariant.** Some PLMs produce embeddings with very
   different L2 norms across positions (especially if some residues
   sit near attention boundaries). Cosine ignores the norm and asks
   only about direction.
2. **Decomposable.** Cosine similarity of L2-normalised vectors is
   just a dot product:

   $$\text{cos}(\mathbf{u}, \mathbf{v}) = \tilde{\mathbf{u}}^\top \tilde{\mathbf{v}}, \qquad \tilde{\mathbf{u}} = \mathbf{u} / \lVert \mathbf{u} \rVert$$

   So once you've normalised both sides, the full $L_a \times L_b$
   similarity matrix is one matrix multiplication: $S = \tilde{A} \tilde{B}^\top$.

Other distance choices are reasonable too:

- **Euclidean distance** is sensitive to magnitude. Useful when norms
  encode information (rare for PLMs).
- **Dot product (unnormalised)** is what attention uses internally
  before the $\sqrt{d_k}$ scaling and softmax. It's more "raw" but
  noisier across positions.
- **Manhattan / cosine in PCA space** is a cheap dimensionality
  reduction trick — project both embeddings into the top-$k$ PC
  subspace before comparing. Makes sense when you have a lot of pairs.

We use cosine throughout this course because it's what every PLM
similarity tutorial uses and because it's what most empirical PLM
benchmarks report.

## What does the embedding actually contain?

A useful exercise: imagine the 1280-dim embedding for a residue is
arranged into 1280 "feature detectors" the model has learned. Empirical
analyses of PLM embeddings (Vig et al, Rao et al, Rives et al) suggest
the dimensions encode roughly:

- Amino-acid identity (~20 dimensions).
- Local secondary-structure preference (~20 dimensions).
- Burial / surface accessibility.
- Disorder propensity.
- Local sequence context features (e.g. "this position sits in a
  hydrophobic cluster").
- Higher-order features extending up to global fold class and family
  membership.

Plus a long tail of less interpretable features, all of which
contribute marginally to the model's downstream predictions. Linear
probes (training a small linear classifier on the embeddings) recover
canonical biological annotations — secondary structure, contact maps,
function — at much higher accuracy than the same probe applied to
one-hot encodings of the raw sequence.

## Why the conserved motif pops out

The `WGK` motif at the start of the E-helix is conserved across the
globin family for structural reasons (it sits at a critical kink
between helices A and E). When ESM-2 was trained on millions of
globin sequences, every time the model saw a `WGK` the gradient
signal pushed those positions' embeddings towards a specific direction
in the 1280-dim space — call it the "globin-WGK direction".

When we evaluate two new globin sequences, both `W` residues at their
conserved positions land near this direction. Their cosine similarity
is high (0.94 in the example output). Same for the `G` and `K` of the
motif.

Less-conserved positions land in more dispersed regions of the
embedding space; their cosine similarities are correspondingly lower
(0.5-0.7 typically) and noisier across runs.

## Layer choice: which to extract from?

ESM-2 650M has 33 transformer blocks. You can extract embeddings
after any layer. A few rules of thumb:

| Use case | Reasonable layer |
|---|---|
| Linear probing for SS / contacts | Mid-to-late: 25-32 |
| Variant-effect zero-shot scoring (PLL) | Final layer: 33 |
| Sequence-level embedding (e.g. for clustering) | Average of middle layers, or final `<cls>` |
| Visualisation / interpretability | Anywhere — they all encode something |

For this module we use layer 33 (the final layer) for simplicity, but
in real-world pipelines mid-layer extraction is often the better
default.

## Pooling: from per-residue to per-sequence

Sometimes you want a single vector per protein, not one per residue.
Standard pooling strategies:

- **Mean pool** over residues. Simple, often effective.
- **`<cls>` token's embedding.** ESM-2 was *not* trained with a
  classification objective so the `<cls>` pool isn't as useful as in
  BERT, but it still works.
- **Max pool** over residues. Sensitive to outlier residues.
- **Attention pooling.** Train a small attention layer on top of the
  per-residue embeddings to weight them. The most expressive option;
  requires a labelled downstream task.

For module 22's downstream pipeline (lead optimisation), the typical
choice is mean-pool the embeddings of an evotuned PLM and feed the
result into a regression head.

## Quick sanity-check questions

If your code prints the cross-similarity matrix and the answer doesn't
look right, things to check:

- **Did you remove `<cls>` / `<eos>`?** If they're still in your
  embedding tensors, the high cosine similarity between two `<cls>`
  vectors will dominate the top-5.
- **Did you normalise both sides?** Skipping the normalisation gives
  you raw dot products, which favour residues with large embedding
  norms.
- **Are the indices 1-based or 0-based?** Easy to off-by-one. Print
  the actual residue letters along with the indices to catch this.
- **Did you load `EsmModel` (not `EsmForMaskedLM`)?** `EsmModel`
  returns `.last_hidden_state` directly; `EsmForMaskedLM` returns
  logits and you'd need to dig into `output_hidden_states=True` to
  recover the embeddings.
- **Is the model on the same device as the inputs?** If `inputs` is on
  GPU but the model is on CPU (or vice versa), you'll get a runtime
  error. `tokenizer(...).to(device)` and `model.to(device)` need to
  agree.

## Embeddings vs attention maps

A historical note. The Rao et al 2021 paper showed that the *attention
maps* of pretrained ESM contain enough signal to predict residue
contacts, even though embeddings would be the more "obvious" choice.
The two are deeply related: attention is the mechanism that produces
embeddings (each layer's output is mostly attended values), so any
information in the embeddings is also encoded somewhere in the
attention pattern of the previous layer.

For practical applications, embeddings are usually more convenient
than attention maps because they're a single vector per residue rather
than an $L \times L$ matrix per layer per head. But if you ever need
to understand *which positions* drive a particular embedding feature,
the attention maps are where you look.
