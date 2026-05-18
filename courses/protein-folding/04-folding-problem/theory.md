## CASP scoring metrics in a bit more detail

CASP has a few standard metrics. You'll see them in papers.

**GDT_TS** (Global Distance Test, Total Score) — the average percentage of
residues that, after optimal superposition, have their alpha carbons
within $1$, $2$, $4$, and $8\ \text{Å}$ of the true position. The
canonical "headline number". Range: 0–100.

$$\text{GDT\_TS} = \frac{1}{4}\sum_{c \in \{1, 2, 4, 8\}} \%(\text{CA within } c\ \text{Å})$$

**TM-score** (Template Modelling score) — a length-normalised structural
similarity score. Range: 0–1.

- $\text{TM-score} < 0.17$: random.
- $0.5 \le \text{TM-score}$: same fold.
- $\text{TM-score} \ge 0.9$: experimental-quality match.

$$
\text{TM-score} = \max_{\text{align}} \left[ \frac{1}{L_{\text{ref}}}
\sum_{i \in \text{aligned}} \frac{1}{1 + (d_i / d_0)^2} \right]
$$

where $d_i$ is the per-residue distance after superposition and $d_0$ is
a length-dependent scale factor.

**lDDT** (local Distance Difference Test) — a *local* score that doesn't
require global superposition. Compares pairwise distances within a small
window. Robust to domain motions. Range: 0–100.

**pLDDT** — the *predicted* lDDT, output by AlphaFold2 and ESMFold per
residue as a confidence estimate. We use it in module 19.

## Co-evolution: the pre-AlphaFold deep insight

The conceptual ancestor of AlphaFold2's MSA stack is **co-evolutionary
analysis**, which was the dominant pre-AlphaFold approach (and is still
the source of most of AlphaFold2's predictive power).

The intuition: when two residues are in direct physical contact in the
folded structure, a destabilising mutation at one position is often
"rescued" by a compensating mutation at the other. Over evolutionary time,
this leaves a statistical signature in the MSA: the two columns are
*correlated*.

But raw column-pair correlations are very noisy — they pick up indirect
correlations (A correlates with B, B correlates with C, so A appears to
correlate with C even though A and C aren't in contact). The methods that
worked were those that fitted a **global statistical model** to the MSA
and read off the "direct" couplings between columns:

- **Direct Coupling Analysis (DCA)** — fits a Potts model (pairwise
  exponential-family distribution over the MSA) and uses the inverse
  correlation matrix as a contact predictor.
- **PSICOV** — similar idea with a sparse-precision regulariser.
- **GREMLIN** — same idea, $L_1$-regularised pseudo-likelihood fit.
- **EVfold** (Sander lab) — couples this to fold-prediction with the
  predicted contacts as constraints.

These methods worked surprisingly well — they could fold small proteins
from sequence alone in the early 2010s. But they required *deep* MSAs
(thousands of homologs) to work well, which excludes most novel proteins.

AlphaFold2 takes this Potts-model perspective and replaces the
hand-engineered statistical model with a learned transformer. The
**Evoformer** does essentially the same job as DCA, but with billions of
parameters and an end-to-end training objective. The performance jump
came partly from MSAs (already a known trick) and partly from finally
having the right neural architecture.

## RoseTTAFold and the open-source response

In 2021, the **Baker lab** at the University of Washington released
**RoseTTAFold**, an architecturally similar (three-track network with
sequence, MSA, and 2D distance representations) but smaller, open-source
model. RoseTTAFold isn't quite as accurate as AlphaFold2, but the source
code and weights were available from day one, which catalysed the
open-source protein ML ecosystem.

David Baker shared the 2024 Nobel Prize with Hassabis and Jumper, partly
for RoseTTAFold and partly for his decades of work on Rosetta-based
protein design (ProteinMPNN, RFdiffusion — both of which we'll meet in
Part 5).

## The Anfinsen-style training-set caveat

Every ML structure prediction model is trained on the PDB. The PDB is
heavily biased:

- Toward proteins that **crystallise well** — typically rigid, soluble,
  globular.
- Toward **single-domain** examples — most multi-domain proteins won't
  crystallise as a whole.
- Toward **medically or industrially relevant** proteins — disease
  targets, well-studied enzymes.
- Away from **disordered**, **membrane-embedded**, and **transient
  complex** proteins.

This bias means the models do best on what they were trained on (small
globular soluble proteins) and progressively worse on harder cases.
Membrane proteins were a known weakness until AlphaFold-Multimer added
substantial data; ESM3 explicitly trains on a much broader structural
distribution.

## Critical caveats around "the problem is solved"

The headline "AlphaFold2 solved protein folding" is a useful shorthand
but it's also a press-release oversimplification. Things still not solved:

- **Multi-domain conformational change.** AlphaFold2 gives you one
  static structure. Real proteins move.
- **Intrinsically disordered regions.** AlphaFold2 honestly predicts
  "low confidence" but doesn't give you a useful ensemble.
- **Multi-chain assemblies and complex stoichiometries.** AlphaFold-
  Multimer / AlphaFold3 improve this but it's far from solved.
- **Protein–small-molecule interactions.** AlphaFold3 added some ligand
  support; this is the new frontier.
- **Designability** — given a target structure, generate a sequence that
  will fold into it. AlphaFold2 doesn't do this directly; ProteinMPNN,
  RFdiffusion, ESM3 do (with various trade-offs).
- **Function prediction** — knowing the structure doesn't always tell
  you what the protein does. This is where multimodal models like ESM3
  start to help.

The folding problem is solved enough that "what is this protein's
structure?" is no longer the central question of computational biology.
The central questions now are about dynamics, design, and function.

## Why this matters for the rest of the course

Almost every module from here on assumes some part of this story:

- Modules 5–8 use **Biopython** to manipulate sequences and structures
  — the lingua franca of computational biology since long before
  AlphaFold.
- Modules 9–14 build up to **ESM-2 and ESM3** — the protein language
  models that replaced MSAs.
- Modules 15–17 do the AlphaFold2 internals in detail — the MSA
  representation, the Evoformer block, and the outer-product-mean trick.
- Modules 20–22 cover **protein design and lead optimisation** — what
  comes after structure prediction.
