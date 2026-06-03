# Structure Quality Metrics

## RMSD: the deceptively simple metric

For two structures with $N$ atom pairs, RMSD is the root-mean-square
deviation of corresponding atom positions:

$$\text{RMSD} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} \lVert p_i - q_i \rVert^2}$$

If the structures are not aligned, you first apply the optimal rigid
transformation (rotation + translation) that minimises this quantity.
The classical algorithm is **Kabsch alignment** (Kabsch 1976):

1. Translate both structures so their centroids are at the origin.
2. Compute the cross-covariance matrix $\mathbf{H} = \sum_i p_i q_i^\top$.
3. SVD: $\mathbf{H} = \mathbf{U} \mathbf{\Sigma} \mathbf{V}^\top$.
4. The optimal rotation is $\mathbf{R} = \mathbf{V} \mathbf{D} \mathbf{U}^\top$ where $\mathbf{D} = \text{diag}(1, 1, \det(\mathbf{V}\mathbf{U}^\top))$ (the determinant correction prevents reflection).

After applying $\mathbf{R}$ to one structure, RMSD is computed
directly. Most production tools (PyMOL's `align`, `lddt`, `tmscore`)
do Kabsch internally.

For our toy exercise we skip Kabsch because the structures are
already aligned and the additional refinement would change the RMSD
by < 0.02 Å — a small effect that adds a lot of code without
improving pedagogy.

### RMSD's pitfalls

RMSD is the most-used structural metric and the most-criticised:

1. **Sensitive to outliers.** A single residue 20 Å off the rest
   dominates the average. The "RMSD = 5 Å" headline can hide
   "structure is mostly perfect except this one floppy loop".
2. **No size normalisation.** RMSD = 5 Å on a 50-residue protein is
   a disaster; on a 1000-residue protein it's reasonable.
3. **Implicit one-to-one correspondence.** If you misnumber residues
   between two structures, RMSD becomes meaningless. Sequence
   alignment must precede coordinate alignment.
4. **Doesn't capture topology.** Two structures with identical
   sequence but completely different folds can have RMSD = 5 Å
   (after alignment) just because the alignment found a partial
   match.

These caveats motivated the development of more robust metrics like
TM-score and lDDT.

## TM-score: the size-normalised cousin

Zhang & Skolnick, 2004, introduced TM-score:

$$\text{TM-score} = \max_{\text{align}} \frac{1}{L_{\text{target}}} \sum_{i=1}^{L_{\text{aligned}}} \frac{1}{1 + (d_i / d_0(L_{\text{target}}))^2}$$

where:

- $L_{\text{target}}$ is the target structure's length (the
  reference, not the prediction).
- $d_0(L) = 1.24 \cdot (L - 15)^{1/3} - 1.8$ is a length-dependent
  scale parameter that grows slowly with protein size.
- $d_i$ is the distance between aligned atom $i$ in the two
  structures.
- The maximum is over all alignments (sequence-based, structural, or
  both — depends on the exact tool).

Properties:

- **Bounded in $[0, 1]$**, with 1 = identical structures.
- **Roughly comparable across protein sizes** because $d_0$ scales
  with $L$.
- **Robust to outliers**, because the per-atom contribution
  saturates at 1 even for $d_i = 0$ and asymptotes to 0 for large
  $d_i$.

The Zhang/Skolnick rule of thumb:

- TM-score > 0.5: same fold, statistically significant.
- TM-score > 0.8: very similar (typically same family).
- TM-score < 0.17: random / unrelated.

For our toy exercise we use a fixed $d_0 = 2.0$, which is *much*
smaller than the real $d_0$ would be for any real-world protein.
This makes the metric more sensitive to small deviations in our
toy — a good pedagogical choice but not directly comparable to
published TM-scores.

## GDT_TS: the CASP standard

Until AlphaFold2, the dominant metric in CASP competitions was
**GDT_TS** (Global Distance Test, Total Score):

$$\text{GDT\_TS} = \frac{1}{4}\!\left[\frac{n_1}{L} + \frac{n_2}{L} + \frac{n_4}{L} + \frac{n_8}{L}\right] \times 100$$

where $n_d$ is the number of residues whose CA atoms are within
$d$ Å of the true position after optimal alignment. So GDT_TS
ranges 0-100; it averages the fraction of residues within 1, 2, 4,
8 Å of true position.

GDT_TS is more discriminating than RMSD at the high-quality end of
predictions: it's nearly saturated at 95+ for AlphaFold2, while
RMSD continues to drop slightly. CASP's classical "this prediction
is essentially correct" threshold is GDT_TS > 90.

GDT_TS isn't included in the exercise but you'll see it in any
AlphaFold2 / ESMFold / RoseTTAFold paper.

## lDDT: the local metric

Mariani et al, 2013, introduced **lDDT** (Local Distance Difference
Test):

$$\text{lDDT}_i = \text{average}\!\left[\,\mathbb{1}[\, |D_{ij}^{\text{pred}} - D_{ij}^{\text{ref}}| < \tau \,]\,\right]_{j: D_{ij}^{\text{ref}} < R, \tau \in \{0.5, 1, 2, 4\}}$$

In words: for each residue $i$, look at all other residues $j$
within reference radius $R = 15$ Å. For each such pair, count it
"good" if the difference between predicted and reference distances
is within $\tau$. Average over $\tau \in \{0.5, 1, 2, 4\}$ Å.

lDDT is **superposition-free** — it doesn't require Kabsch
alignment because it operates on pairwise distances rather than
absolute positions. This makes it robust to multi-domain
flexibility (a hinged protein that's "right" in shape but "wrong"
in inter-domain orientation gets a high lDDT but a low RMSD).

**pLDDT** (AlphaFold / ESMFold) is the model's prediction of what
lDDT would be against the (unknown) ground truth. Calibrated
during training so that the predicted score matches the actual
expected accuracy.

## RMSD vs TM-score vs lDDT: when to use which

| Metric | Best for | Worst for |
|---|---|---|
| RMSD | Quick comparison after alignment | Multi-domain flexibility, outliers |
| TM-score | Cross-protein comparison, fold classification | Hinge-bend within same fold |
| lDDT | Local structural quality, hinge-bend handling | Computing ranks across many predictions |
| GDT_TS | High-quality prediction discrimination (CASP) | Low-quality predictions, fast triage |

In ML papers benchmarking structure prediction:

- AlphaFold-family papers report GDT_TS prominently.
- ESMFold and recent papers report TM-score and lDDT.
- For per-residue analysis, pLDDT is the standard.

## Why fixed $d_0$ in our toy

For real-world proteins, the variable $d_0(L)$ in TM-score is
crucial — it makes TM-score comparable across protein sizes.
With $d_0(L) = 1.24 \cdot (L - 15)^{1/3} - 1.8$:

| $L$ | $d_0$ |
|---|---|
| 50 | 1.34 |
| 100 | 3.15 |
| 200 | 4.85 |
| 500 | 7.85 |
| 1000 | 10.07 |

Notice $L = 50$ gives only $d_0 \approx 1.34$, but for $L < 15$ the
formula gives non-real / negative numbers. The TM-score authors
typically clamp $d_0$ to a minimum of 0.5 for very short fragments.

For our 5-residue toy, the formula gives nonsense, so we use the
arbitrary fixed value $d_0 = 2.0$. The metric is still sensible —
it's bounded in $[0, 1]$ and reduces to the standard form — but
the absolute values aren't comparable to published TM-scores on
real proteins.

## Reading pLDDT distributions

Tools like AlphaFold's confidence viewer plot pLDDT vs residue
index. Common shapes:

- **Globular protein**: high pLDDT throughout (often 80-95), with
  small dips at flexible loops and termini.
- **Multi-domain protein**: high pLDDT within each domain, sharp
  drops at inter-domain linkers.
- **IDR (intrinsically disordered region)**: long stretches of
  pLDDT < 50, often at the N- or C-terminus.
- **Membrane protein**: high pLDDT in the transmembrane core, lower
  in the loops.

For a downstream consumer of predicted structures, the basic
quality filter is "drop residues with pLDDT < 70". For a strict
filter, "drop entire predictions with mean pLDDT < 70". These rules
of thumb are model-agnostic — they work for AlphaFold2, ESMFold,
RoseTTAFold, and AlphaFold3 alike.

## Beyond this module

Real structure-evaluation pipelines use packages like:

- `lDDT` ([http://lddt.protein-explorer.org/](http://lddt.protein-explorer.org/)) — official local-quality calculator.
- `tmtools` (Python wrapper for TM-align) — superpositional alignment + TM-score.
- `biotite.structure` — production-quality NumPy-native parsing and analysis.
- DeepMind's `OpenStructure` toolkit — comprehensive for serious work.

For most ML applications you'll use these as black-box scoring
functions. The toy implementation in this module is to ensure you
understand what they're computing under the hood.
