## Why the scaling wall happens

The naive scaling-laws picture — borrowed from Kaplan et al's LLM work
and Chinchilla — predicts smooth power-law improvements as you scale
parameters, data, and compute together. For natural-language LLMs that
prediction has held remarkably well. For sequence-only PLMs trained on
UniRef-style corpora it does not.

There are at least three reasons people have advanced to explain why.

### Perplexity ≠ transferability

The MLM objective optimises one quantity: how well the model predicts
masked tokens given surrounding ones. Lower perplexity on UniRef50 says
the model has internalised more of natural sequence statistics. But the
*downstream* tasks we care about — variant-effect prediction, function
classification, fitness regression — depend on properties (structure,
function, fitness under specific assays) that are only indirectly
present in the training signal.

This is exactly the "loss → metric" gap that the AMPLIFY and VespaG
papers highlight empirically: a model can beat ESM-2 on perplexity yet
not transfer better to fitness tasks. As you scale, perplexity keeps
improving, but the *transferable* part of the signal saturates. Past
some point you're paying ever more parameters to fit features that don't
help downstream.

### Phylogenetic noise

UniRef is biased toward what evolution has produced abundantly:
bacterial proteins, well-sequenced organisms, common domains. Past a
certain model size the network has enough capacity to memorise
phylogenetic regularities — "this looks like an E. coli ribosomal
protein" — that correlate with *origin* rather than with *function*.
That memorised information uses parameter budget without helping
transfer.

Curated, deduplicated, function-balanced corpora (the AMPLIFY direction)
help here, but the available datasets are much smaller than UniRef and
shrink the trainable model size.

### Modality mismatch

Natural-language pretraining sees the modality that downstream tasks
also use: text. Protein pretraining sees sequence; downstream tasks
often live in structure or function space. Sequence-only models can
recover a lot of those modalities implicitly (ESM-2 contacts, ESMFold
folding), but each additional layer of implicit recovery pays a
representation-efficiency tax. Structure-aware models cut out that tax
by giving the model the modality it actually needs.

This is the conceptual through-line from module 14: multimodal training
is more parameter-efficient than sequence-only at downstream transfer
because each modality contributes complementary signal that doesn't have
to be reconstructed from another.

## What to do instead of "scale up"

The de facto consensus in 2026 looks something like:

1. **Curate diverse downstream-property datasets.** The bottleneck on
   transfer is not parameter count; it is the availability of well-
   labelled fitness, function, and structure data for evaluation and
   semi-supervised training. ProteinGym is the leading public benchmark
   in this direction.
2. **Add structure or function modalities to the input.** ProSST's
   structure tokens, VespaG's MSA-derived auxiliary targets, and PoET's
   homolog context are all variations on this theme. They consistently
   beat raw scale.
3. **Right-size the backbone.** A 300 M – 650 M structure-aware or
   MSA-conditioned model usually beats a 3 B – 15 B sequence-only model
   on the same task. Inference is cheaper and the failure modes are
   easier to debug.
4. **Use sequence-only billion-parameter models for what they're
   actually good at: generation.** Sampling diverse, plausible-looking
   sequences from a strong sequence prior is still valuable for de novo
   design and ESM3-style controllable generation.

## A quick formal note

A simple way to see the perplexity vs transfer split: under the standard
MLM objective the gradient at every step is

$$\nabla_\theta\, \mathbb{E}_{x \sim D}\!\left[\sum_{i \in \text{mask}} -\log p_\theta(x_i \mid x_{\setminus i})\right]$$

which is a likelihood-ratio gradient with respect to the *training
distribution* $D$. There is no term that ties $\theta$ to the
distribution of downstream tasks. Larger $\theta$ buys more
likelihood under $D$; whether that translates to transfer depends on how
much of $D$'s structure is informative about the task. Past the elbow
in that curve, additional capacity is spent on $D$-specific noise.

## The frontier from here

If you take only one thing from this module: **the field's hypothesis
about how to make better protein models has shifted from "scale up" to
"add modalities, curate data, right-size the backbone"**. Course
modules 9-14 still teach the core machinery; it's the engineering
choices around those ideas that have moved on.

A non-exhaustive list of recent directions worth tracking:

- **Structure-tokenised models** beyond ProSST (e.g. Foldseek-style
  3Di tokenisation feeding into a transformer).
- **Joint diffusion + transformer models** that blur the line between
  ESM3 (discrete denoising) and AlphaFold3 (continuous diffusion), see
  module 24.
- **Long-context PLMs** that ingest very deep MSAs (10⁴+ sequences)
  efficiently — the next generation of PoET-style architectures.
- **Targeted finetuning recipes**: g-DPO (module 22) and its successors
  that align a small base model to a specific assay tend to deliver
  more per-dollar than scaling the base model up.

Module 24 covers the structure-prediction / design side of the same
2024-2026 evolution.
