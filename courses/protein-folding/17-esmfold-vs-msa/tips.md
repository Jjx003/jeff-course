## Going deeper

- **Lin et al, 2023** — *Evolutionary-scale prediction of atomic-level protein structure* — [https://www.science.org/doi/10.1126/science.ade2574](https://www.science.org/doi/10.1126/science.ade2574). The ESMFold paper. Section 3 has the head-to-head comparison with AlphaFold2 across MSA depth regimes.
- **Hayduk's PLM primer Part III** — covers the ESMFold story and the implicit-MSA argument with extra narrative detail.
- **Jumper et al, 2021** — [https://www.nature.com/articles/s41586-021-03819-2](https://www.nature.com/articles/s41586-021-03819-2). For the AlphaFold2 side of the comparison.
- **Abramson et al, 2024** — *Accurate structure prediction of biomolecular interactions with AlphaFold 3* — [https://www.nature.com/articles/s41586-024-07487-w](https://www.nature.com/articles/s41586-024-07487-w). For comparing to the latest from DeepMind.
- **ColabFold** — [https://github.com/sokrypton/ColabFold](https://github.com/sokrypton/ColabFold). The community-friendly AlphaFold2 alternative with MMseqs2-based MSA search. Worth running once even just to see what an MSA pipeline looks like in practice.
- **ESM Atlas** — [https://esmatlas.com/](https://esmatlas.com/). EvolutionaryScale's database of 600M+ ESMFold-predicted structures from metagenomic sources. A demonstration of the throughput advantage in action.

## Common confusions

### "ESMFold doesn't see *any* MSA, ever?"

Correct. At inference time, ESMFold consumes a single sequence.
During *training*, ESMFold's PLM (ESM-2) was trained on UniRef
sequences which collectively span MSA-like homology relationships,
but the model never saw an explicit MSA — only individual sequences
sampled in batches.

A subtle point: ESM-2 doesn't even use the *fact* that two sequences
are homologous. The training distribution makes homologous sequences
appear with similar contexts, but the model doesn't know which
sequence came from which family.

### "If ESM-2 has implicit co-evolution, why isn't it perfect?"

The information capacity of the weights is finite. ESM-2 15B has
$\sim 60$ GB of parameters in FP32; the explicit MSAs of the 50M
training sequences amount to far more raw data than that. Compression
loses information.

The key empirical observation is *how much* is preserved: enough that
ESM-2's contact-prediction accuracy from attention maps is comparable
to MSA-based DCA. Enough, but not perfect. There's a regime where
the explicit MSA still helps (deep MSAs of well-studied families).

### "Could you bridge the two — give ESMFold an MSA at inference?"

Yes, and people have tried. The MSA Transformer (Rao et al, 2021) is
explicitly designed to consume MSAs. ESM-MSA (a variant) does
similarly. These hybrid systems sit between AlphaFold2 and ESMFold
in the speed/accuracy plot.

Empirically, providing an MSA to a large pretrained PLM helps a bit
on deep-MSA proteins and helps not at all on shallow-MSA proteins.
The diminishing returns of MSA augmentation are why the field has
mostly moved on from explicit MSA inputs except for the highest-
accuracy applications.

### "Doesn't a single forward pass mean less reasoning?"

You'd think so, but ESM-2's 33-layer (650M) or 48-layer (15B)
transformer is doing a lot of work in that single pass. Each layer
refines the per-residue representation by attending across all
positions. After 33-48 layers, the representation has been
"recycled" through attention and FFN many times — equivalent to
several iterations of explicit refinement.

AlphaFold2's 48 Evoformer blocks × 3 recycling passes = 144 effective
attention/FFN cycles. ESMFold's 33-48 PLM layers × 8 IPA layers ≈
40-50 cycles. The depth is comparable; AlphaFold2 just spreads it
over fewer parameters per layer.

### "How big is the structure module compared to the PLM?"

The PLM dominates. ESM-2 15B is 15 billion parameters; ESMFold's
structure module is on the order of $10^7$-$10^8$ parameters. The
folding-specific machinery is a small bolt-on; almost all the model
capacity is in the language model.

This is why "fold a protein" with ESMFold is essentially equivalent
to "run ESM-2" plus a thin decoder.

## Things to do before module 18

Module 18 actually loads ESMFold and runs it on a small peptide.
Things to confirm before you start:

1. You have ~16 GB of free disk space for the ESMFold + ESM-2
   weights.
2. You have a GPU with $\ge 8$ GB VRAM (16 GB strongly recommended).
   CPU inference is technically possible but very slow for ESMFold.
3. You're comfortable with PyTorch's `model.eval()` /
   `torch.no_grad()` idioms (we used them in modules 11-13).

The exercise will pre-arrange the input sequence and the chunk-size
flag for OOM protection. If your GPU has less than 16 GB, you can
still run the exercise on the recommended 30-residue peptide; longer
sequences may need to be skipped.
