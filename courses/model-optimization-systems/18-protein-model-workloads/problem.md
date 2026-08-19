# Protein model workloads

LLM optimization ideas transfer to protein modeling, but never one-to-one.
Proteins are token sequences, yet protein workloads are not just "chat
completion with amino acids." Some tasks look like encoder inference. Some look
like all-atom geometric prediction. Some require database search before the
neural network even runs. Some produce confidence scores that are useful only if
you understand what benchmark and biological question they came from.

This reading maps the inference ideas from the first half of the course onto
modern protein and biomolecular models:

- ESMFold-style single-sequence structure prediction,
- AlphaFold2-style MSA-heavy folding,
- AlphaFold3-style biomolecular complex prediction,
- Chai-1-style accessible multimodal structure prediction,
- Boltz-style open biomolecular foundation models with affinity heads,
- protein language model embedding and variant scoring,
- high-throughput screening pipelines for design and drug discovery.

The systems question is: **which part of the pipeline is expensive, and what
can be batched, cached, quantized, packed, or skipped without breaking the
biology?**

## A workload map

| Workload | Typical input | Typical output | Systems bottleneck |
|---|---|---|---|
| Protein language model embedding | One or many amino-acid sequences | Per-residue or pooled embeddings | Transformer FLOPs, sequence length, padding waste |
| Variant effect prediction | Wild-type sequence plus mutations | Fitness, pathogenicity, or likelihood score | Many related sequences, reuse opportunities |
| Single-sequence folding | One protein sequence | 3D coordinates plus confidence | Long-sequence attention, structure module |
| MSA-based folding | Sequence plus evolutionary homologs | 3D coordinates plus confidence | MSA/template search, pair memory, recycling |
| Complex prediction | Multiple chains, ligands, nucleic acids, ions | Joint 3D complex | Pair features, atom features, diffusion/refinement |
| Binding affinity prediction | Protein-ligand or protein-protein pair | Affinity or ranking score | Data quality, calibration, physics realism |
| Protein design | Desired structure/function constraints | New sequence or backbone | Many candidates, expensive verification |

The optimization strategy changes with the row. Packing helps pure sequence
embedding. It may be unsafe or unsupported in all-atom complex prediction.
Quantization can help an embedding model while subtly changing downstream
ranking. MSA caching can dominate AlphaFold2-style throughput but does almost
nothing for a single-sequence PLM route.

![Log-log chart of relative cost against chain length for linear, quadratic, and cubic terms, beside a table listing which cost term each pipeline stage pays](/courses/model-optimization-systems/protein-cost-profile.svg)

The chart is the reason this module exists as something other than an LLM
appendix. In language modeling the worst term you normally meet is $O(L^2)$,
and the entire attention-kernel literature exists to tame it. Folding models
have an $O(L^3)$ term, and it is not an implementation detail — it comes from
the triangle operations that give the pair representation its geometric
consistency, so it cannot be tiled away without changing the model.

The practical consequence is that the toolbox from the first half of this course
attacks the *middle* rows of that table and leaves the top and bottom alone.
FlashAttention improves the $O(sL^2c)$ MSA attention. Quantization improves the
per-parameter cost of the trunk. Neither touches the $O(L^3c)$ triangle updates,
and neither touches the database search that often dominates a single cold
request. Reaching for a kernel optimization before profiling is, in this domain,
a good way to make the fast part faster.

## ESMFold-style systems

ESMFold showed that a large protein language model can predict structure
directly from sequence, avoiding explicit MSA search. That matters because MSA
search can be the slowest part of a traditional folding pipeline. A PLM has
absorbed evolutionary signal during pretraining, so inference can become closer
to a large transformer forward pass plus a structure head.

The tradeoff is familiar:

- **Speed and scale.** Single-sequence models are attractive when you need to
  annotate millions of proteins or scan many variants quickly.
- **MSA-poor proteins.** If evolutionary homologs are scarce, an MSA-based model
  may not have much signal to exploit.
- **Accuracy limits.** For proteins with deep MSAs and familiar folds,
  AlphaFold2-style systems can still be stronger.
- **Long sequences.** Transformer attention and memory still scale with length,
  so batching, packing, and FlashAttention-style kernels matter.

In optimization terms, ESMFold-like workloads look more like encoder inference
than autoregressive decode. There is no KV cache growing token by token. The
main levers are batching, sequence length management, kernel efficiency, and
possibly quantization that preserves representation quality.

## AlphaFold3-style systems

AlphaFold3 expanded the prediction target from protein-only structures to
biomolecular interactions involving proteins, DNA, RNA, small molecules, ions,
and chemical modifications. That makes the model much more useful for biology
and drug discovery, but it also makes the systems problem less like plain
sequence modeling.

An AlphaFold3-style request may include:

- multiple protein chains,
- nucleic acid chains,
- ligands and cofactors,
- ions,
- post-translational modifications,
- templates or user-specified constraints depending on the implementation.

The output is not merely a sequence-level class label. It is a joint 3D object
with atom coordinates, chain interfaces, and confidence estimates. The model
must represent residue-residue, atom-atom, and molecule-molecule relationships.
The expensive tensors often scale with pair or atom interactions, not just token
count.

This is why naive LLM tricks can mislead. You cannot automatically pack two
independent complexes into the same attention window unless the model and masks
were built to prevent cross-complex leakage. You cannot judge ligand docking
from pLDDT alone. You cannot assume that lower perplexity on protein sequences
means better interface geometry.

## Chai and Boltz in the open ecosystem

Chai-1 and Boltz-style models matter because they made high-end biomolecular
prediction more accessible to builders outside a single proprietary stack.
Chai-1 presented an openly accessible multimodal foundation model for molecular
structure prediction. Boltz-1 and Boltz-2 pushed an open AlphaFold3-like line of
work further, with Boltz-2 emphasizing binding affinity prediction in addition
to structure.

For a systems engineer, the key point is not "which model wins forever." It is
that the workload is becoming richer:

- structure prediction plus confidence,
- complexes rather than single chains,
- ligands and nucleic acids,
- constraints and templates,
- affinity or ranking heads,
- many generated candidates that need triage.

By 2026, a serious protein optimization stack is usually a cascade. It may use a
PLM to score or embed a large candidate set, a structure model to fold the most
promising candidates, an all-atom or affinity model to rank interactions, and
experimental feedback to close the loop.

## What "state of the art" means here

In LLM serving, a benchmark might ask for tokens/sec, latency, or pass@k. In
biomolecular modeling, "SOTA" depends on the scientific question:

- monomer fold accuracy,
- multimer interface accuracy,
- ligand pose quality,
- nucleic acid interaction quality,
- mutation effect ranking,
- binding affinity calibration,
- success rate in wet-lab validation.

Those are not interchangeable. A model can produce beautiful monomer structures
and still rank binders poorly. A model can place a backbone correctly and miss a
small-molecule pose. A high-confidence prediction can reflect training-set
familiarity rather than the biological mechanism you care about.

This is the main caveat for the rest of the course: optimization must preserve
the measurement that matters. Faster wrong biology is not a win.

## Recap

Protein-model optimization is an applied systems problem with biological
constraints. ESMFold-like workloads reward sequence batching and transformer
efficiency. AlphaFold2-style workloads are shaped by MSA search, pair memory,
and recycling. AlphaFold3, Chai, and Boltz-style workloads add multimolecular
inputs, all-atom geometry, constraints, and affinity-like outputs.

The next lab tackles one simple but high-impact systems trick: reducing padding
waste when batching variable-length protein sequences. It also settles the
question that makes the trick safe to use, by running a real ESM-2 checkpoint and
checking whether a packed sequence's embeddings match the ones it gets when
processed alone.
