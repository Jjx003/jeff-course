## Goal

Use ESM-2 650M as a **zero-shot variant-effect predictor**. Given a
wild-type sequence and a few single-point mutants, compute each
sequence's **pseudo-log-likelihood (PLL)** and confirm that
mutations at conserved positions score worse.

This is the building block under the Cradle "logiter" approach
(module 22) — the model never saw the protein during training, never
saw any assay data, but its log-probabilities still rank sequences
in a way that correlates with fitness.

![Myoglobin structure, PDB ID 1MBN](/courses/protein-folding/myoglobin-1mbn.png)

*Variant-effect scoring starts from a sequence, but the reason mutations
matter is that they perturb a folded molecule. Structure image from PDBe/RCSB
PDB, PDB ID `1MBN`.*

## The PLL formula

For a sequence $x = (x_1, \ldots, x_L)$, the **pseudo-log-likelihood**
under a masked language model is:

$$\text{PLL}(x) = \sum_{i=1}^{L} \log p(x_i \mid x_{\setminus i})$$

For each position $i$:

1. Replace $x_i$ with `<mask>` and feed the resulting sequence to
   the model.
2. Read off the log-probability that the model assigns to the
   correct residue $x_i$ at position $i$.
3. Sum across all positions.

**Important:** PLL is **not** a true log-likelihood (the
factorisation across positions is wrong because each conditional is
re-mixed with all the others). But it's a cheap surrogate that
empirically tracks the true likelihood for evaluating mutations.

The *delta* between mutant and wild-type is the relevant signal:

$$\Delta\text{PLL} = \text{PLL}(\text{mutant}) - \text{PLL}(\text{wild-type})$$

A negative $\Delta\text{PLL}$ means the model thinks the mutation is
unlikely / unfit; a positive value means it's plausible.

## Setup

- **Hardware**: NVIDIA GPU with ~6 GB VRAM. CPU works but is
  glacially slow (~30 s per masked forward pass = ~30 minutes for
  a 30-residue sequence).
- **Model**: `esm2_t33_650M_UR50D` (33 layers, 650 M parameters).
- **Wild-type sequence**: same myoglobin N-terminal fragment as
  module 11 — `MGLSDGEWQLVLNVWGKVEADIPGHGQEVL` (30 residues).

We define four mutants for variety:

| Variant ID | Mutation | What it does |
|---|---|---|
| `W8A` | W at position 8 → A | Replace conserved aromatic — drastic |
| `W15A` | W at position 15 → A | Same; another conserved aromatic |
| `K17R` | K at 17 → R | Conservative (positive → positive) |
| `A20V` | A at 20 → V | Modest size change |

Position numbering is 1-indexed (so `position 8` is the 8th residue
of the wild-type string). On a full-length protein the tryptophan
knockouts (`W8A`, `W15A`) typically score clearly worse than wild-type
and the conservative `K17R` stays close to neutral.

> **Caveat — this is a 30-residue fragment, not a full protein.** ESM-2
> conditions each masked prediction on the rest of the sequence, and a
> short isolated fragment supplies much weaker context than the intact
> myoglobin chain. On this fragment the per-variant ΔPLL values are
> small and noisy, and the *sign* of an individual mutation can even
> flip. That is expected: the robust "conserved tryptophan is hard to
> substitute" signal emerges on full-length sequences and when averaged
> over many variants. What this module teaches is the **mechanics of
> PLL scoring**; treat the exact numbers below as illustrative of the
> output format, not as a guaranteed ranking for this short input.

## What to compute

For each sequence (WT + 4 mutants):

1. For every position $i$ in the sequence:
   - Build a copy of the sequence with position $i$ masked.
   - Run ESM-2 once.
   - Extract the model's log-probability for the actual residue at
     position $i$.
2. Sum across positions to get the PLL.
3. Compute $\Delta\text{PLL}$ relative to wild-type.

## Required output (illustrative, not byte-exact)

```text
ESM-2 650M pseudo-log-likelihood scoring
Wild-type sequence (length 30):
MGLSDGEWQLVLNVWGKVEADIPGHGQEVL

Computing PLL for 5 sequences x 30 positions = 150 forward passes ...

  WT     PLL = -52.341
  W8A    PLL = -64.873   delta = -12.532
  W15A   PLL = -65.124   delta = -12.783
  K17R   PLL = -53.205   delta =  -0.864
  A20V   PLL = -54.918   delta =  -2.577

Ranking (most likely first):
  1. WT       PLL = -52.341
  2. K17R     PLL = -53.205
  3. A20V     PLL = -54.918
  4. W8A      PLL = -64.873
  5. W15A     PLL = -65.124
```

The exact numerical values vary across GPUs and `transformers`
versions; expected output is omitted for this reason.

## What you should learn

- **Zero-shot variant effects.** ESM-2 was never trained on
  myoglobin specifically, never saw any fitness assay, never saw
  any wet-lab data. Its log-probabilities still rank tryptophan-to-
  alanine mutations as worse than conservative changes, simply
  because tryptophan-at-conserved-positions is universal across the
  globin family in its training corpus.
- **Cost.** PLL needs $L$ forward passes per sequence. For a 30-residue protein, that's manageable; for a 1000-residue protein,
  600 GPU-seconds per sequence isn't free. Production tools amortise
  by computing PLL once for wild-type and only re-evaluating the
  affected positions for each mutant.
- **Calibration.** PLL is not a true likelihood. The absolute number
  has limited meaning; the *difference* from wild-type is what
  matters.
- **Generalisation to assays.** PLL correlates with deep-mutational-
  scanning data (Hopf et al, 2017; Riesselman et al, 2018; Meier et
  al, 2021). It's not as good as a model fine-tuned on the assay,
  but it's a free baseline.

## Trick: efficient PLL via batching

Naively, you'd loop over positions and run one forward pass per
mask. But ESM-2 can mask multiple positions at once and run a single
forward pass. Each masked position only sees other positions
unmasked, but if you mask too many, the predictions become noisy
because the conditioning context shrinks.

A common trade-off:

- **One position at a time**: $L$ forward passes, perfectly accurate.
- **All positions at once**: 1 forward pass, but each prediction
  conditions on a heavily-masked context. Substantially less
  accurate; effectively a different metric.
- **Random subset masking (each position once across multiple
  passes)**: e.g. $\lceil L / 10 \rceil$ forward passes with 10% of
  positions masked each. Good speed-quality balance.

Our exercise uses the strict "one position at a time" approach —
slow but mathematically equivalent to the formal PLL definition.
