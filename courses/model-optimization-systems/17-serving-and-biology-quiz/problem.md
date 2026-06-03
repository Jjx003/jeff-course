# Serving and biology checkpoint

This checkpoint reviews the second half of the course, where the focus shifted
from model weights and fine-tuning to inference systems and biomolecular
workloads.

The quiz covers:

- FlashAttention and online softmax,
- KV-cache memory and long-context serving,
- paged cache management,
- continuous batching,
- speculative decoding,
- protein language model workloads,
- sequence packing,
- AlphaFold/Chai/Boltz-style systems intuition.

The goal is not to memorize product names. The goal is to classify an
optimization by the constraint it relaxes. When you can do that, the details
become much easier to remember.

## How to think during the quiz

For each question, ask three things:

1. **Which phase is being optimized?** Prefill, decode, fine-tuning, embedding,
   folding, screening, or scheduling?
2. **Which resource is scarce?** FLOPs, memory bandwidth, HBM capacity, wall
   clock latency, preprocessing time, or biological labels?
3. **What correctness contract must survive?** Exact attention, target-model
   distribution, independent sequence masking, valid geometry, or honest
   validation split?

Those questions are more reliable than matching buzzwords.

## Serving concepts to review

Modern LLM inference is usually split into prefill and decode. Prefill processes
the prompt and builds the initial KV cache. Decode appends one or more generated
tokens while reusing the cache. That split explains why some optimizations help
long prompts, while others help the one-token-at-a-time generation loop.

FlashAttention belongs to the family of exact attention algorithms that reduce
memory traffic by tiling and maintaining online softmax statistics. It is not an
approximation to attention; it is a different way to compute the same result
more efficiently.

Paged cache management and continuous batching are serving-layer ideas. They do
not make the model smarter. They make it possible to keep memory organized and
GPU work flowing as requests start, stop, and grow at different rates.

Speculative decoding is a latency idea. A cheap proposal mechanism tries to let
one target-model verification step commit multiple output tokens. It is useful
only when accepted-token gain exceeds draft overhead.

## Biology concepts to review

Protein-model optimization starts with shapes:

- sequence representations scale roughly with $L$,
- attention over a sequence can scale with $L^2$,
- pair representations in structure models often scale with $L^2d_\text{pair}$,
- MSA tensors add a homolog dimension,
- all-atom complex models add molecule and atom-level structure.

ESMFold-style systems are attractive for fast single-sequence prediction because
they avoid explicit MSA search. AlphaFold2-style systems lean heavily on
evolutionary signal and pair representations. AlphaFold3, Chai, and Boltz-style
systems broaden the target to biomolecular complexes, ligands, nucleic acids,
constraints, and sometimes affinity-like outputs.

The practical systems trick from the last lab was sequence packing. It is a
good fit for independent PLM-style embedding when masks prevent cross-sequence
attention. It is not automatically safe for structure prediction, where pair
features and geometry modules may treat packed residues as part of one molecular
system.

## What completion means

This is a quiz, so you will see feedback as you answer and a summary at the end.
Use misses as a diagnostic. If a question feels ambiguous, identify which
resource or phase you were tracking incorrectly, then revisit the relevant
module.
