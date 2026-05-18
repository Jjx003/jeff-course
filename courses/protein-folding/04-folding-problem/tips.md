## Going deeper

- **Jumper et al., "Highly accurate protein structure prediction with AlphaFold"** (Nature, 2021) — [https://www.nature.com/articles/s41586-021-03819-2](https://www.nature.com/articles/s41586-021-03819-2). The headline AlphaFold2 paper. Dense but worth a careful read once you've finished modules 15-16.
- **Lin et al., "Evolutionary-scale prediction of atomic-level protein structure"** (Science, 2023) — [https://www.science.org/doi/10.1126/science.ade2574](https://www.science.org/doi/10.1126/science.ade2574). The ESMFold paper.
- **Hayes et al., "Simulating 500 million years of evolution with a language model"** (EvolutionaryScale, 2024) — [https://www.evolutionaryscale.ai/blog/esm3-release](https://www.evolutionaryscale.ai/blog/esm3-release). The ESM3 launch post, with the esmGFP case study.
- **AlphaFold Protein Structure Database** — [https://alphafold.ebi.ac.uk/](https://alphafold.ebi.ac.uk/). Free interactive viewer for over 200 million predicted structures. Search by gene name or UniProt ID.
- **CASP results** — [https://predictioncenter.org/](https://predictioncenter.org/). All historical CASP scores and target sequences. Useful if you want to benchmark new methods or just see how the state of the art has progressed.
- **Mohammed AlQuraishi's "AlphaFold2 @ CASP14: It feels like one's child has left home"** — [https://moalquraishi.wordpress.com/2020/12/08/alphafold2-casp14-it-feels-like-ones-child-has-left-home/](https://moalquraishi.wordpress.com/2020/12/08/alphafold2-casp14-it-feels-like-ones-child-has-left-home/). The classic blog post capturing the immediate post-CASP14 mood from a leading academic predictor.

## Things to remember

- The **"AlphaFold solved folding"** narrative is a useful shorthand but
  not a complete story. Static single-chain prediction is solved; dynamics,
  multi-state proteins, and design are open.
- **CASP scores are blind**. If a paper claims a high accuracy number
  without using a CASP target (or some other temporally-held-out
  benchmark), be skeptical — many overfit-to-training-set numbers float
  around the literature.
- **The PDB is biased.** Predictions of soluble globular proteins are
  much more reliable than predictions of membrane proteins, disordered
  regions, or transient complexes.
