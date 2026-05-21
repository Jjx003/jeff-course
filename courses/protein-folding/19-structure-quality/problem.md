## Goal

Three short tasks, all on toy embedded PDB structures so the output
is fully deterministic:

1. **RMSD** between two pre-aligned 5-residue structures (a "true"
   reference and a "predicted" model).
2. A simple **TM-score-like** metric on the same pair.
3. **pLDDT distribution analysis** on a third structure that has
   pLDDT values stored in the B-factor column (AlphaFold / ESMFold
   convention).

## Why these three metrics?

- **RMSD (Root Mean Squared Deviation)** is the most common
  pairwise structural-similarity metric. Easy to compute, but its
  units (Ångströms) and unboundedness make it hard to interpret
  across proteins of different sizes.
- **TM-score** is the standard "size-normalised" similarity metric.
  Bounded in $[0, 1]$ where higher is more similar. We compute a
  simplified version with a fixed $d_0$.
- **pLDDT** is the AlphaFold / ESMFold per-residue confidence score,
  stored in the B-factor column of the predicted PDB. Reading the
  distribution is essential for interpreting any predicted structure.

## Input — three embedded PDBs

The starter file embeds three short PDB strings.

### TRUE structure (a 5-residue alpha-trace)

```text
R1 at (0.0, 0.0, 0.0)
R2 at (3.8, 0.0, 0.0)
R3 at (7.6, 0.0, 0.0)
R4 at (11.4, 0.0, 0.0)
R5 at (15.2, 0.0, 0.0)
```

Five residues in a perfectly straight line along $x$, 3.8 Å apart.

### PREDICTED structure (slightly off in $z$)

```text
R1 at (0.0, 0.0, 0.0)        (perfect)
R2 at (3.8, 0.0, 0.0)        (perfect)
R3 at (7.6, 0.0, +1.0)       (1 A above)
R4 at (11.4, 0.0, -1.0)      (1 A below)
R5 at (15.2, 0.0, 0.0)       (perfect)
```

A symmetric "kink" in the middle that doesn't affect the endpoints.

### pLDDT structure (5 residues, AlphaFold-style)

A separate PDB whose ATOM lines have pLDDT in the B-factor column:

```text
R1: pLDDT 88.0
R2: pLDDT 75.0
R3: pLDDT 62.0
R4: pLDDT 92.0
R5: pLDDT 81.0
```

The coordinates of this structure are irrelevant for the analysis;
we only read the B-factors.

![Protein contact map, PDB ID 2QIP chain A](https://commons.wikimedia.org/wiki/Special:Redirect/file/Protein_Contact_Map%2C_2-Color%2C_2QIP-A.png)

*A contact map reduces a 3D protein structure to residue pairs that are close
in space. Image from Wikimedia Commons, Chuck.sweet, CC BY-SA 3.0.*

## RMSD formula

For $N$ atom pairs $(p_i, q_i)$ assumed to be already optimally
aligned:

$$\text{RMSD} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} \lVert p_i - q_i \rVert^2}$$

For our two structures:

- Per-residue distances: $0, 0, 1, 1, 0$
- $\text{RMSD} = \sqrt{(0 + 0 + 1 + 1 + 0) / 5} = \sqrt{0.4} \approx 0.6325$ Å

> **Important caveat:** real RMSD computation would first do
> **Kabsch alignment** to find the optimal rotation that minimises
> the deviation. Our two toy structures are already aligned (same
> centroid, mostly the same axis), so we skip the alignment step in
> this exercise. Theory.md walks through what Kabsch would do.

## TM-score-like formula

A simplified version of the standard TM-score:

$$\text{TM-like}(d_0) = \frac{1}{L} \sum_{i=1}^{L} \frac{1}{1 + (d_i / d_0)^2}$$

with $d_i$ the per-residue distance (after alignment) and $d_0$ a
length-normalisation parameter. The real TM-score uses
$d_0(L) = 1.24 \cdot (L - 15)^{1/3} - 1.8$ for $L > 15$, which is
ill-defined for our 5-residue toy. We use a **fixed $d_0 = 2.0$ Å**
for simplicity.

For our pair with distances $[0, 0, 1, 1, 0]$:

$$\text{TM-like}(2.0) = \frac{1}{5}\!\left[1 + 1 + \frac{1}{1.25} + \frac{1}{1.25} + 1\right] = \frac{4.6}{5} = 0.92$$

## pLDDT analysis

Walk the third PDB's ATOM lines, extract the B-factor of each unique
residue, and compute:

- Mean, min, max.
- Fraction with pLDDT > 70 (the "confident" threshold).
- Fraction with pLDDT > 90 (the "very high confidence" threshold).

For our values $[88, 75, 62, 92, 81]$:

- Mean: $79.6$
- Min / max: $62.0 / 92.0$
- Fraction $> 70$: $4/5 = 0.80$
- Fraction $> 90$: $1/5 = 0.20$

## Required output (exact)

```text
RMSD computation
  Atoms compared: 5
  Per-residue distances (A): [0.000, 0.000, 1.000, 1.000, 0.000]
  RMSD: 0.6325 A

TM-score-like metric (d_0 = 2.000)
  Score: 0.9200

pLDDT analysis
  Residues: 5
  Mean pLDDT: 79.60
  Min pLDDT:  62.00
  Max pLDDT:  92.00
  Fraction with pLDDT > 70: 0.80 (4/5)
  Fraction with pLDDT > 90: 0.20 (1/5)
```

## What you should learn

- **RMSD is a one-line formula** but interpretation needs care:
  units are Å, magnitude depends on protein size, and small RMSD
  can hide locally bad regions (think a single rigid body with one
  flapping loop).
- **TM-score is bounded** in $[0, 1]$ and roughly comparable across
  proteins. > 0.5 means "same fold" by the original Zhang/Skolnick
  definition; > 0.8 means "very similar". The full formula uses a
  $d_0$ that scales with protein length; ours is a fixed-$d_0$
  simplification.
- **pLDDT is per-residue and lives in the B-factor column** in
  AlphaFold / ESMFold predictions. Mean pLDDT > 70 is "good"; > 90
  is "publication-quality"; below 50 means the model is uncertain
  and you shouldn't trust the local geometry.
- **The B-factor column reuse** is non-standard from a
  crystallographer's perspective — be aware when you mix predicted
  and experimental structures in the same downstream pipeline.
