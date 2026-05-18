## When to choose what

A practical decision guide for picking a PLM in 2026, given the
landscape this module describes.

### For embeddings and representations

- **Default: ESMC 300 M.** It matches ESM-2 650 M quality at roughly
  half the size and is faster at inference. Non-commercial licence is
  fine for research and personal projects.
- **Need a permissive licence (commercial use, redistribution): ESM-2
  650 M.** Still solid, MIT licensed, well-supported in HuggingFace.
- **Need the absolute best representation, and licence permits: ESMC
  6 B** via Forge / SageMaker. The 6 B → 600 M gain is real but small;
  the 6 B → 300 M gain is larger.

### For fitness prediction (zero-shot variant effects)

- **Default: a structure-aware model.** ProSST currently leads
  ProteinGym at 110 M parameters; VespaG (a tiny head on frozen
  ESM-2 650 M) is the top sequence-only entry. Either is a better bet
  than a larger sequence-only PLM.
- **If you have a deep MSA and can afford the inference cost: an
  MSA-conditioned PLM** like PoET or E1. These typically out-score
  sequence-only models when good MSAs are available.
- **If you have to use sequence-only and can't afford structure
  inference**, stop at ESM-2 650 M / ESMC 300 M. Going bigger does not
  reliably help fitness benchmarks.

### For generation (de novo design, sampling)

- **ESM3** if its non-commercial licence works for you and you want
  multimodal conditioning.
- Otherwise **ESM-2 + fine-tuning** (evotuning, g-DPO, module 22) is
  still the workhorse. The scaling wall hurts transfer more than it
  hurts generation; ESM-2 at 650 M – 3 B remains useful for sampling.

### A short reminder

Bigger is no longer the safe default for protein language models, and
neither is sequence-only training. Choose the smallest model with the
right modalities for your task, fine-tune it carefully, and put the
saved compute into curating data instead.

## Common confusions

### "Did ESM-2 stop being useful?"

No. ESM-2 is still the MIT-licensed open baseline, the model most
implementations target, and a reasonable choice for representation work
and generation. What changed is that you should no longer assume "use
the biggest ESM-2 you can fit" is the best move. The 650 M model has
become the practical sweet spot and ESMC 300 M is the modern equivalent.

### "Does the scaling wall also apply to AlphaFold3 / Boltz-2?"

The scaling wall as described here is specifically about
**sequence-only PLMs trained with the MLM objective**. Structure
prediction models like AlphaFold3 and Boltz-2 have their own scaling
behaviour, which is dominated by data quality (number of high-resolution
PDB structures, diversity of complexes) and architectural choices, not
by parameter count alone. Module 24 covers this in more detail.

### "Why does ProSST peak at 110 M when ESM-2 keeps improving to 3 B?"

Two reasons. First, ProSST's training corpus is ~19 M AlphaFold DB
structures — much smaller than UniRef50's ~50 M sequences. With less
data, the optimal model size is smaller. Second, ProSST's effective
input dimensionality is higher (sequence + structure + position tokens),
which gives more bits per residue and saturates earlier on parameter
count.

### "What about Profluent's E1 / ProGen3 / other proprietary models?"

These are real and competitive, but most are gated or commercial-only.
For self-driven learning the open ProteinGym leaderboard is the most
useful reference because every entry has an open paper and most have
weights you can run. Commercial models will out-score open ones on some
benchmarks; the *architecture lessons* from the open work transfer
either way.

### "Is the scaling wall going to be 'unbroken' eventually?"

Possibly, with better data, multimodal training, or curriculum-style
scaling. The current consensus is that *under the current MLM-on-UniRef
recipe* the wall is real. Under a different recipe — much more diverse
data, structure tokens, function tokens — the wall might move, but
those recipes are exactly what ESM3, ProSST, and PoET are exploring,
and they don't need 10 B+ parameters to work.

## Going deeper

- **Alex Rogozhnikov — *State of the wall in protein language models in 2026*** — [https://arogozhnikov.github.io/2026/02/01/protein-lms.html](https://arogozhnikov.github.io/2026/02/01/protein-lms.html). Comprehensive review of the scaling wall and the structure-aware / MSA-conditioned alternatives. Excellent reading-list anchor for this module.
- **Pascal Notin — *Have we hit the scaling wall for protein language models?*** — [https://pascalnotin.substack.com/p/have-we-hit-the-scaling-wall-for](https://pascalnotin.substack.com/p/have-we-hit-the-scaling-wall-for). The late-2025 essay that crystallised the scaling-wall framing for the field, drawing on the ProteinGym leaderboard.
- **EvolutionaryScale — ESM Cambrian 600 M (HuggingFace)** — [https://huggingface.co/EvolutionaryScale/esmc-600m-2024-12](https://huggingface.co/EvolutionaryScale/esmc-600m-2024-12). The official release page for ESMC 600 M, with the 300 M variant linked alongside. Includes the "ESMC 300 M matches ESM-2 650 M" benchmark plot.
- **ProteinGym leaderboard** — [https://www.proteingym.org/](https://www.proteingym.org/). The standardised benchmark every model in this module is evaluated against. Worth scrolling through to see which architectures actually dominate.
- **Li et al, 2024 — *Structure-informed Language Models (ProSST)*** — [https://arxiv.org/abs/2405.15793](https://arxiv.org/abs/2405.15793). ProSST's structure-token PLM with separate attention over sequence and structure.
- **Fournier et al, 2024 — *Protein Language Models Need Better Data, Not More (AMPLIFY)*** — [https://arxiv.org/abs/2410.16729](https://arxiv.org/abs/2410.16729). The data-quality-over-quantity counterpoint.
- **Marquet et al, 2024 — *VespaG: Tiny adapters on PLM embeddings*** — [https://www.biorxiv.org/content/10.1101/2024.04.24.590982](https://www.biorxiv.org/content/10.1101/2024.04.24.590982). The "tiny head on ESM-2 beats huge sequence-only models" approach.
- **Truong & Bepler, 2023 — *PoET: A generative model of protein families as sequences-of-sequences*** — [https://arxiv.org/abs/2306.06156](https://arxiv.org/abs/2306.06156). The original MSA-conditioned PLM.
- **Profluent E1** — see Profluent Bio's release notes and the
  Rogozhnikov review above for the current published numbers.

## Things to try after

- Pick one of the ProteinGym benchmark splits, download the
  predictions for ESM-2 650 M, ESMC 300 M, and ProSST, and compute the
  Spearman correlations yourself. The relative rankings tend to match
  the leaderboard headline numbers, and reading the per-dataset spread
  is the fastest way to build intuition for which models excel where.
- Replace ESM-2 in module 18 (ESMFold) or module 22's evotuning step
  with ESMC 300 M and re-run. Most code paths transfer cleanly —
  EvolutionaryScale's API mirrors HuggingFace conventions.
- Read the Rogozhnikov post in full and try to articulate, in one
  paragraph, why a 110 M ProSST beats a 15 B ESM-2 at variant-effect
  prediction. The exercise sharpens intuition for the modality
  argument.
