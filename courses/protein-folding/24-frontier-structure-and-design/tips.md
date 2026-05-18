## When to choose what

Quick-reference picks for 2026 structure-prediction and design work.

### Structure prediction

- **You need commercial use rights → Boltz-2.** MIT-licensed,
  AF3-class quality, full code and weights open. Default for any
  production workflow.
- **You need to predict DNA / RNA / small-molecule / metal complexes →
  AlphaFold3 if license permits, otherwise Boltz-2.** Both handle the
  full chemistry uniformly via the diffusion module.
- **Quick triage on lots of orphan proteins → ESMFold (module 18) is
  still acceptable.** No MSA search, single forward pass, fast. Quality
  is lower than AF3 / Boltz-2 but the throughput is unbeatable for
  large-scale screening.
- **You're learning and just want the simplest example → ESMFold.**
  Module 18 remains the cleanest "PLM as implicit MSA database"
  demonstration; the Boltz-2 codebase is substantially heavier.

### Inverse folding

- **Standard backbone, no special context → ProteinMPNN.** Module 21
  still applies.
- **Binding site contains a ligand, cofactor, or metal →
  LigandMPNN.** The recovery jump (especially for metals) is large
  enough that you almost always want this when the input PDB has any
  non-protein atom.
- **Designing a soluble cytosolic protein → SolubleMPNN.** Fixes the
  surface-hydrophobic bias of plain ProteinMPNN.

### De novo design

- **General de novo binder / enzyme / DNA-binding protein →
  RFdiffusion3.** Atom-level, 10× faster than RFdiffusion2, SOTA on
  37 / 41 enzyme-scaffold benchmarks. One tool for most design
  workflows.
- **The classic round-trip:**
  RFdiffusion3 → LigandMPNN → Boltz-2 → optional g-DPO loop. Each step
  has open weights; the whole pipeline can be run from a single
  workstation.

### Lead optimisation

- **The course's module 22 framing still applies.** The pipeline
  diagram is unchanged; the CRADLE-1 preprint just adds peer-track
  evidence. If you're starting from scratch in 2026, follow the
  CRADLE-1 paper for the architecture rather than the older Magnus
  Ross blog (which remains an excellent intro).

## A short reminder

The 2024-2026 frontier is unambiguous about one engineering choice:
**use the smallest specialised model that has the right inputs**.
LigandMPNN beats bigger inverse-folding models because it has a ligand
channel. Boltz-2 beats bigger sequence-only structure predictors
because it has explicit pair + diffusion machinery. ProSST and VespaG
(module 23) beat bigger PLMs because they have structure or MSA
context. The pattern is the same across both modules of this
"frontier" pair.

## Common confusions

### "Is Boltz-2 just an open AlphaFold3?"

Architecturally similar (Pairformer-style trunk, diffusion module) but
independently trained on different data with different hyperparameters.
Quality is comparable on most benchmarks; AF3 has a small edge on some
exotic ligand and PTM cases, Boltz-2 has the edge on binding-affinity
prediction. The MIT license is the deciding factor for most
practitioners.

### "Why is LigandMPNN's metal recovery jump so much larger than the small-molecule jump?"

Metal-coordination chemistry is heavily constrained: a Zn²⁺ ion is
nearly always coordinated by His / Cys / Asp / Glu in a tight
tetrahedral or square-planar geometry. Once the model sees the metal,
the choice of side chain collapses to a few options. Small molecules
have more flexibility (multiple plausible binding modes, more side-
chain options at the interface), so even with ligand context recovery
is harder.

### "Is RFdiffusion3 going to replace ProteinMPNN entirely?"

No — they solve different problems. RFdiffusion3 generates a **3-D
structure** (atoms in space); ProteinMPNN / LigandMPNN assigns a
**sequence** to an existing backbone. A typical design pipeline runs
RFdiffusion3 first to make a structure, then LigandMPNN to assign a
sequence to it. The two tools are complements, not competitors.

### "What about AlphaFold-Multimer and AlphaFold2?"

AF-Multimer is now subsumed by AF3 / Boltz-2 (both handle multimers
natively). Plain AF2 is still useful if you specifically want the
classical Evoformer + structure-module pipeline — for instance, when
you're following along with modules 15-16 or doing research on AF2's
internals — but for production structure prediction it has been
superseded.

### "Does the CRADLE-1 paper change anything from module 22?"

The pipeline architecture is the same. What changed: CRADLE-1
quantifies success rates (90-95 % vs ~85 % rational-design baseline)
across many more campaigns than were public when module 22 was first
written, and g-DPO now has its own theoretically grounded paper. If
you're citing module 22's pipeline in your own work, CRADLE-1 and the
g-DPO paper are the primary references to use.

## Going deeper

- **Abramson et al, 2024 — *Accurate structure prediction of biomolecular interactions with AlphaFold 3*** — [https://www.nature.com/articles/s41586-024-07487-w](https://www.nature.com/articles/s41586-024-07487-w). The AF3 paper itself; chapter on the diffusion module is the key reading.
- **Boltz-2 preprint, June 2025** — [https://www.biorxiv.org/content/10.1101/2025.06.14.659707](https://www.biorxiv.org/content/10.1101/2025.06.14.659707). The open AF3-class model that most teams actually run. Includes the FEP-comparable binding-affinity numbers.
- **Boltz GitHub** — [https://github.com/jwohlwend/boltz](https://github.com/jwohlwend/boltz). Code and weights, MIT license. `pip install boltz` to get started.
- **Dauparas et al, 2025 — *LigandMPNN*** (Nature Methods) — [https://www.nature.com/articles/s41592-025-02626-1](https://www.nature.com/articles/s41592-025-02626-1). The ligand-aware ProteinMPNN successor. Reports the 63 / 50 / 77 % recovery numbers.
- **LigandMPNN GitHub** — [https://github.com/dauparas/LigandMPNN](https://github.com/dauparas/LigandMPNN). Reference implementation, includes SolubleMPNN as a configuration flag.
- **RFdiffusion3 announcement (IPD, December 2025)** — [https://www.ipd.uw.edu/2025/12/rfdiffusion3-now-available/](https://www.ipd.uw.edu/2025/12/rfdiffusion3-now-available/). Project page with the 10× speed-up, atom-level diffusion, and the 37 / 41 enzyme-benchmark numbers.
- **RFdiffusion2 (Nature Methods, 2025)** — [https://www.nature.com/articles/s41592-025-02975-x](https://www.nature.com/articles/s41592-025-02975-x). The atom-level enzyme-active-site scaffolding paper. Useful for understanding the RFdiffusion → 2 → 3 progression.
- **CRADLE-1 preprint, March 2026** — [https://www.biorxiv.org/content/10.64898/2026.03.06.710001v2.full](https://www.biorxiv.org/content/10.64898/2026.03.06.710001v2.full). The Cradle team's own write-up of the Logiter pipeline from module 22. Includes the 90-95 % success-rate numbers across commercial campaigns.
- **Magnus Ross — *An idiot's guide to lead optimisation, Part 1*** — [https://magnusross.github.io/posts/protein-lead-optimisation-1/](https://magnusross.github.io/posts/protein-lead-optimisation-1/). The original blog that module 22 was built on. Still the clearest pedagogical walk-through of the pipeline.

## Things to try after

- Install Boltz-2 (`pip install boltz`) and re-run module 18's ESMFold
  example side by side. Compare wall-clock time, pLDDT scores, and
  RMSD against the experimental structure if you have one.
- Take a small PDB structure containing a metal ion and run plain
  ProteinMPNN vs LigandMPNN on it. Compare the recovered sequences at
  the coordinating residues. The qualitative difference is more
  striking than the headline number suggests.
- Read the AF3 paper's diffusion section alongside the AF2 structure-
  module section. The conceptual jump from "frame composition + torsion
  angles" to "denoise atom coordinates" is the single biggest
  architectural shift in protein ML since the Evoformer.
- If you're feeling ambitious: take the design loop described in this
  module (RFdiffusion3 → LigandMPNN → Boltz-2) and try a toy de novo
  binder against a small target. Every component has open weights; the
  pipeline runs on a single consumer GPU; the experience of seeing the
  three models hand off structures to each other is the closest you
  can get to a modern lab's design workflow without a wet lab.

Thanks for taking this update tour. The frontier moves fast, but the
mental model you've built across the first 22 modules is exactly what
you need to read next year's papers as they appear. Go build something.
