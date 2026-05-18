## Vector-quantised autoencoders, in detail

The structure tokenisation in ESM3 borrows the **VQ-VAE** technique
from generative image modelling (van den Oord et al, 2017).

### The discrete bottleneck

A standard variational autoencoder maps an input $\mathbf{x}$ to a
continuous latent $\mathbf{z} \in \mathbb{R}^d$, then back. A VQ-VAE
adds a **quantisation step**: the continuous latent $\mathbf{z}_e$
is replaced by its nearest neighbour in a learned **codebook**
$\{\mathbf{e}_1, \dots, \mathbf{e}_K\}$:

$$\mathbf{z}_q = \mathbf{e}_{k^*}, \qquad k^* = \arg\min_k \lVert \mathbf{z}_e - \mathbf{e}_k \rVert_2$$

The decoder reconstructs $\mathbf{x}$ from $\mathbf{z}_q$ alone. The
loss has three terms:

$$\mathcal{L} = \underbrace{\lVert \mathbf{x} - \hat{\mathbf{x}} \rVert^2}_{\text{reconstruction}} + \underbrace{\lVert \text{sg}[\mathbf{z}_e] - \mathbf{e}_{k^*} \rVert^2}_{\text{codebook}} + \beta \underbrace{\lVert \mathbf{z}_e - \text{sg}[\mathbf{e}_{k^*}] \rVert^2}_{\text{commitment}}$$

where $\text{sg}[\cdot]$ is the stop-gradient operator. The first
term trains the encoder/decoder; the second moves codebook entries
toward the encoder outputs; the third encourages the encoder to
commit to a codebook entry.

After training, **the codebook entries become a discrete vocabulary**.
For ESM3, this vocabulary represents structural neighbourhoods — each
entry is a "type" of local backbone geometry the model has clustered
during training.

### Codebook size

ESM3 uses a structure codebook of about 4096 entries. The trade-off:

- **Larger codebook** → finer structural distinctions, more tokens,
  longer effective sequence length.
- **Smaller codebook** → blunter structural representation, more
  "structure as text" framing, shorter sequences.

4096 lands in a sweet spot: enough to distinguish helices from sheets
from loops, and to make finer distinctions like "alpha-helix
position $i+1$" vs "alpha-helix position $i+4$" vs "G-shaped beta
turn".

## Function tokens, in detail

The function vocabulary is a union of several smaller taxonomies:

### Per-residue tokens

- **DSSP secondary structure** (8 classes: H, B, E, G, I, T, S, -)
- **Solvent accessibility** (binned: buried / partially buried /
  exposed)
- **Active-site / catalytic-residue flags**
- **Post-translational modification site** (phosphorylation,
  glycosylation, etc.)
- **Disulfide partner** (which other residue, if any, it pairs with)
- **InterPro residue-level annotations** (specific motif positions)

### Per-protein tokens

- **GO molecular function** (~40,000 terms, hierarchical)
- **GO biological process** (~30,000 terms, hierarchical)
- **GO cellular component** (~5,000 terms, hierarchical)
- **InterPro family / superfamily / domain** (~50,000 entries)
- **EC number** (enzyme classification, ~6,000 entries)

Each protein in the training set is annotated with a subset of these.
The model is trained to:

- Predict missing function tokens given sequence + structure (this is
  effectively a function-prediction task).
- Generate sequence/structure consistent with a given function token
  set (the design direction).

Sparsity is a real challenge. A typical protein in the training set
has only 5-20 function tokens out of the full vocabulary; the model
has to handle very sparse conditioning at inference time.

## Conditional generation, in detail

ESM3's inference is essentially "iterative denoising": fill in the
masked tokens by repeatedly predicting them, in a strategy similar to
**MaskGIT** or **discrete diffusion**:

1. Start with a fully-masked target (all `<mask>` in the channels
   you want to generate).
2. Predict probabilities over all masked positions.
3. Commit (sample / argmax) the **most-confident** predictions.
4. Iterate. At each step, more positions are committed and fewer
   are masked.
5. Stop when no more masks remain.

This iterative strategy lets the model "decide easy positions first"
and then propagate that information to harder positions. The
alternative (autoregressive single-pass generation) is also possible
but less effective for the multi-modal joint distribution.

## Sampling temperature

Like every generative LM, ESM3 has a sampling-temperature knob. Low
temperature ($T \to 0$) means greedy decoding — deterministic, the
single most likely sequence. High temperature ($T \to \infty$) means
uniform sampling — chaotic.

For real protein design, intermediate temperatures (~0.5-1.0) are
typical. You sample $N$ candidate designs in parallel, then score them
with structure-prediction models or wet-lab assays.

## The "compressed database" view at three modalities

Module 10's framing translates cleanly:

- **In ESM-2**, attention queries match against a database of
  *sequence patterns*.
- **In ESM3**, attention queries match against a database of joint
  (sequence, structure, function) patterns. The database is much
  bigger because the joint space is bigger; the patterns are richer
  because they encode structural / functional context.

A single attention head in ESM3 can in principle learn behaviours
like "if the structure tokens at $i$ and $j$ both correspond to
beta-strand geometry, attend to $j$ when predicting the amino-acid
token at $i$" — directly equivalent to "predict beta-sheet pairing
partners".

## Implementation note: model availability

ESM3's full weights are not as freely available as ESM-2 (some
checkpoints require an EvolutionaryScale Forge account or commercial
license). The open-source `esm` package (now under EvolutionaryScale
ownership) exposes a small ESM3 demo model; production-grade
checkpoints currently sit behind an API.

For the rest of this course we use ESM-2 / ESMFold rather than ESM3
because the open-source story is much cleaner. The conceptual
framework you've built up — fuzzy matching, compressed databases,
multi-stream attention — applies directly when you do gain access to
ESM3.

## How ESM3 relates to AlphaFold3

AlphaFold3 (DeepMind, 2024) is a parallel "everything-multimodal"
system, also covering sequence + structure + function but with a
different architectural lineage. Some differences:

- **AlphaFold3 keeps the AlphaFold2 Evoformer-style** pair
  representation as a core data structure; ESM3 dispenses with it in
  favour of plain-transformer multi-stream tokens.
- **AlphaFold3 supports ligand and nucleic-acid prediction**
  natively; ESM3 v1 is protein-focused.
- **AlphaFold3's training data overlaps heavily with ESM3's** but the
  training objective is different (diffusion-based for AlphaFold3,
  discrete denoising / MLM for ESM3).

Both systems represent the current state-of-the-art at the date of
writing this course. They will be superseded; the conceptual
multimodality is here to stay.
