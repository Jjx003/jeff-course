# Practical hints

## Choosing the right metric

Before optimizing a protein model workload, name the unit of success:

| Task | Useful metrics |
|---|---|
| PLM embedding | residues/sec, sequences/sec, embedding quality on downstream task |
| Variant scoring | rank correlation, top-k recall, assay split validity |
| Monomer folding | pLDDT, TM-score, lDDT, runtime per sequence |
| Complex prediction | DockQ, interface RMSD, chain placement accuracy |
| Ligand pose prediction | ligand RMSD, pocket validity, chemistry sanity checks |
| Affinity prediction | correlation, calibration, enrichment, target split performance |

Do not optimize tokens/sec if the actual product decision depends on recovering
active binders.

## Batching advice

- Bucket proteins by length before batching.
- Report both sequences/sec and residues/sec.
- Separate preprocessing time from neural-network time.
- Cache MSAs, templates, embeddings, and featurized inputs when reuse is real.
- Track peak memory as well as average latency.
- Measure padding waste explicitly before implementing sequence packing.

## Biological caveats

- Intrinsically disordered regions may be low confidence because they do not
  have one stable structure.
- Membrane proteins, flexible complexes, and transient interactions can behave
  differently from soluble globular proteins.
- A confident monomer structure does not guarantee a correct binding interface.
- Ligand pose and binding affinity are related but not the same problem.
- Wet-lab validation remains the final judge for design and drug discovery.

## Transition

The next module focuses on a narrow setting where a standard systems trick is
safe: packing independent protein sequences for language-model-style embedding.
Keep the caveats in mind. The technique is powerful, but only when the model's
masking semantics make independence explicit.
