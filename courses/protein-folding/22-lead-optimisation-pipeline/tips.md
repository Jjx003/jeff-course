## Common confusions

**"Is g-DPO doing reinforcement learning?"**

Conceptually yes — DPO is the offline form of preference-based RL.
Mechanically no — you're doing supervised learning with a
specific log-ratio loss. There's no rollout, no reward model, no
exploration in the RL sense. You feed in (winner, loser) pairs and
gradient-descend on the DPO loss like any other supervised task.

**"Why isn't the predictor just a fine-tuned ESM-2 head with
regression?"**

It is — that's exactly what it is. The "predictor" is just the
evotuned PLM (frozen) plus a small MLP head trained on assay data.
Calling it a separate model is a diagram convenience; in code it's
a head + a frozen base.

**"Is logiter the same as ESM-2?"**

No, but it's *built from* ESM-2. The logiter's pipeline is:

ESM-2 (modules 9-11) -> evotune on family MSA (module 7+15) -> g-DPO on assay pairs -> logiter

Each step modifies the weights. You end up with a model that's
ESM-2-like in architecture but quite different in what it
predicts at each position.

**"Where does inverse folding (ProteinMPNN, module 21) fit in?"**

Cradle's published pipeline (as of Magnus Ross's writeup) doesn't
use inverse folding directly. But it's complementary: you could
add it as an alternative generation source. Sample sequences for
the template's known backbone via ProteinMPNN, then rank with the
predictor. This is part of "generation" in the diagram if you
choose to include it.

**"Why bother with evotuning if we have assay data?"**

Three reasons:

1. **Assay data is scarce** (96 sequences per plate, weeks per
   plate). MSAs typically have $10^3-10^5$ sequences. Evotuning
   exploits the larger MSA before assay data even arrives.
2. **Cold-start.** Round 1 of generation has *no* assay data; you
   have to bootstrap from somewhere.
3. **Generalisation.** Evotuning gives the model knowledge of
   *natural* variation. g-DPO makes it specialise on *our* assay.
   Without evotuning the model would happily propose totally
   non-natural mutations that look great on the assay but fail in
   downstream contexts (manufacturability, in-vivo stability).

**"What's the difference between RFdiffusion and Cradle's pipeline?"**

Different problems entirely. RFdiffusion (Watson et al, 2023)
designs *new backbones* from scratch — you give it a target
function and it produces a 3-D structure. ProteinMPNN then
samples sequences for that backbone (module 21). Cradle's pipeline
optimises an *existing* protein's sequence for an *existing*
function — no new backbones generated. The two are complementary:
RFdiffusion + ProteinMPNN for de novo design; Cradle for lead
optimisation of natural / existing scaffolds.

**"Could we replace the predictor with the logiter's own
log-probability?"**

Empirically no, at least not by itself. PLL (module 20) correlates
roughly with fitness for natural-like proteins, but the
correlation breaks down once you push into novel sequence space —
which is exactly where lead optimisation lives. The supervised
predictor head is calibrated against your specific assay; PLL is
calibrated against "what UniRef50 looks like". Both signals are
useful; combining them tends to outperform either alone.

## Going deeper

- **Magnus Ross — *An idiot's guide to lead optimisation for proteins, Part 1*** — [https://magnusross.github.io/posts/protein-lead-optimisation-1/](https://magnusross.github.io/posts/protein-lead-optimisation-1/). The blog post this module is based on. Part 2 (when it appears) will cover the generation step in more detail.
- **Cradle whitepaper** — [https://www.cradle.bio/](https://www.cradle.bio/). Cradle's company-facing description of the pipeline. Light on technical detail, but the diagrams and high-level claims align with Magnus Ross's writeup.
- **Rafailov et al, 2023** — *Direct Preference Optimization: Your Language Model is Secretly a Reward Model* — [https://arxiv.org/abs/2305.18290](https://arxiv.org/abs/2305.18290). The foundational DPO paper. The derivation in section 4 is the core math you should understand if you want to follow how g-DPO modifies it.
- **Christiano et al, 2017** — *Deep reinforcement learning from human preferences* — [https://arxiv.org/abs/1706.03741](https://arxiv.org/abs/1706.03741). The classical RLHF approach DPO replaces.
- **Hopf et al, 2017** — *Mutation effects predicted from sequence co-variation* — [https://www.nature.com/articles/nbt.3769](https://www.nature.com/articles/nbt.3769). EVmutation. The pre-PLM approach to fitness prediction.
- **Wu et al, 2019** — *Machine learning-assisted directed protein evolution with combinatorial libraries* — [https://www.pnas.org/doi/10.1073/pnas.1901979116](https://www.pnas.org/doi/10.1073/pnas.1901979116). The classical paper on ML-augmented directed evolution; pre-Cradle, pre-PLM, but the loop structure is recognisable.
- **Yang et al, 2019** — *Machine-learning-guided directed evolution for protein engineering* — [https://www.nature.com/articles/s41592-019-0496-6](https://www.nature.com/articles/s41592-019-0496-6). Frances Arnold lab's review of the area as of 2019.
- **ProteinGym benchmark** — [https://www.proteingym.org/](https://www.proteingym.org/). Standardised evaluation suite for variant-effect predictors. ESM-1v, ESM-2, AlphaFold-based scores, and supervised models all benchmarked head-to-head.
- **Watson et al, 2023** — *De novo design of protein structure and function with RFdiffusion* — [https://www.nature.com/articles/s41586-023-06415-8](https://www.nature.com/articles/s41586-023-06415-8). RFdiffusion paper, for the de-novo-design counterpoint to Cradle's lead-optimisation focus.

## Things to try after

You've reached the end of the course. To make the techniques
stick, build a tiny end-to-end pipeline of your own. A weekend
project sketch:

1. **Pick a small target protein** with a published deep-mutational-
   scanning dataset. ProteinGym has dozens.
2. **Evotune ESM-2 8M** (or 35M) on the target's family using
   MSA data from UniRef. ~1 hour on a single GPU.
3. **Train a predictor head** on a subset of the DMS data (say
   80% train / 20% val).
4. **Score the held-out variants** with both the bare PLL (module
   20) and your trained predictor. Compute Spearman correlation
   with experimental fitness for each.
5. **Compare**: predictor should beat PLL by at least 0.1
   Spearman. If not, debug.

For ambition, add g-DPO on the same data: form pairs, fine-tune
the model with the DPO loss, and re-score. Compare PLL of the
DPO'd model to the original PLL on a different held-out subset.

Bonus round: hook ESMFold (module 18) and module 19's TM-score
into the loop as a structural-quality filter on generated
candidates. Now you have a pipeline that closely mirrors Cradle's
flow chart — minus the wet lab.

Thanks for completing the course. Now go do some protein
engineering.
