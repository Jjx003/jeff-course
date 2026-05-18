## Goal

Run **inverse folding** on a small protein backbone: given a fixed
3-D structure (just the backbone atoms — N, CA, C, O), generate
candidate amino acid sequences that should fold into roughly the
same shape. Print each candidate's per-residue log-probability sum
and its **recovery** (percent identity to the wild-type sequence).

This is the **other half** of the protein-folding pipeline. Modules
11-18 went `sequence -> structure`. ProteinMPNN goes
`structure -> sequence`. Together they let you **redesign** a
protein: take a structure you like, generate sequences that should
fold into it, score them with ESM-2 PLL (module 20), and pick the
best for wet-lab validation.

## Setup

- **Hardware**: the starter ships a deterministic NumPy stub that
  runs in a few milliseconds on CPU — no GPU required. The
  *real* ProteinMPNN model (used optionally as an extension)
  needs an NVIDIA GPU with ~2 GB VRAM. ProteinMPNN is small by
  ML standards — ~1.7 M parameters.
- **Software**: ProteinMPNN ([https://github.com/dauparas/ProteinMPNN](https://github.com/dauparas/ProteinMPNN)).
  Install instructions (only needed if you want to swap out the stub):

  ```bash
  git clone https://github.com/dauparas/ProteinMPNN
  cd ProteinMPNN
  pip install -e .
  # Or (sometimes works):
  # pip install git+https://github.com/dauparas/ProteinMPNN
  ```

  ProteinMPNN's repo isn't a polished pip package; expect minor
  surgery. If you can't get it installed in your environment, use
  the **stub fallback** in the starter (described below).

- **Inputs**: a small PDB structure (we embed a 12-residue toy
  backbone in the script) and a wild-type reference sequence.

## The stub fallback

If ProteinMPNN isn't installed (or `import protein_mpnn` fails),
the script falls back to a **stub** that simulates the inverse-folding flow:

1. For each of 5 candidates, walk the sequence position by position.
2. At each position, sample a residue from a backbone-conditioned
   distribution (we fake this with a slight bias toward the WT
   residue plus Gaussian noise).
3. Sum `log p(aa | backbone)` to get the candidate's total
   log-probability.
4. Report the candidate, its log-prob, and its recovery to WT.

The stub doesn't predict real backbones-to-sequences — it's purely
for letting you exercise the data flow. The real ProteinMPNN's
recovery on average across the PDB is ~50 %; the stub deliberately
hovers around 30-50 % to mimic that range.

## What you should produce

```text
ProteinMPNN inverse folding (stub fallback)
Backbone: 12 residues (chain A)
Wild-type sequence: MAEGLKWIVASR

Sampling 5 candidates at temperature = 1.0 ...
  1. MAEGLKWIVASR  log_prob = -3.142   recovery = 12/12 (100.0%)
  2. MAEGLKHIVASA  log_prob = -8.917   recovery = 10/12 ( 83.3%)
  3. NAEGAKHIIASR  log_prob = -14.583  recovery =  7/12 ( 58.3%)
  4. ...
  5. ...
```

Exact numbers depend on the stub's random draws (we seed numpy for
reproducibility within a single run). The platform does **not**
grade exact values — `expected_output` is omitted.

## Things to read off the output

- **Recovery** — fraction of positions where the sampled sequence
  matches the wild-type. Real ProteinMPNN typically achieves 40-60
  % on standard benchmarks; that's a noisy but useful proxy for
  "are we sampling biologically reasonable sequences?"
- **Log-probability** — total log-probability of the sampled
  sequence under the model. Higher (less negative) means the model
  is more confident the sequence will fold into the given backbone.
- **Sampling temperature** — the script samples at $\tau = 1.0$. Real
  ProteinMPNN runs typically use $\tau = 0.1-0.3$ for high-quality
  designs and $\tau = 1.0$ for diversity.

### Modern successor: LigandMPNN

The Dauparas / Baker lab published **LigandMPNN** (Nature Methods,
2025), a ProteinMPNN successor that adds small-molecule, nucleotide,
and metal-ion context to the input. The recovery jumps at constrained
sites are substantial — 63 % vs 50 % for small molecules, 50 % vs 35 %
for nucleotides, and **77 % vs 36 % for metals** — and LigandMPNN has
been used to design 100+ experimentally-validated binding proteins. A
parallel **SolubleMPNN** variant fixes plain ProteinMPNN's surface-
hydrophobic bias for cytosolic designs. For new work in 2026,
LigandMPNN is the right default whenever the binding site contains a
ligand or cofactor; ProteinMPNN remains the choice for plain backbones.
Module 24 covers the frontier of structure-aware design tools.

## What you should learn

- **Inverse folding is the dual problem.** Forward folding asks
  "what structure does this sequence make?"; inverse folding asks
  "what sequences fit this structure?". Both are learned by similar
  encoder-decoder transformers, just with different I/O.
- **Recovery as a benchmark.** Inverse folding is hard to evaluate
  because there are *many* valid sequences for any given backbone.
  Recovery (against the wild-type sequence) is a tractable proxy
  but mis-specifies the goal — the model isn't *trying* to recover
  WT exactly.
- **Connecting the loop.** ProteinMPNN -> ESMFold -> ESM-2 PLL is
  a complete *design* loop: sample sequences for a backbone, fold
  them, check that the fold matches the input backbone, and score
  the sequences with a fitness proxy. This is what de novo protein
  design pipelines look like in 2024-2025.
- **The Cradle pipeline (module 22) uses a similar pattern,** but
  conditioned on assay data instead of pure log-probabilities.

## Why expected_output is omitted

Three sources of variation:

1. The stub's random seed is set, but FP arithmetic across NumPy
   versions can drift in the 5-6th decimal.
2. Real ProteinMPNN inference is GPU-non-deterministic at the same
   level.
3. Different ProteinMPNN versions have different defaults (chunk
   sizes, masks).

The platform handles missing expected output gracefully and
returns a "pending" verdict.
