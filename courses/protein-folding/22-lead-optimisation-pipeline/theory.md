## A closer look at DPO

Direct Preference Optimisation (Rafailov et al, 2023) was a
breakthrough for LLM post-training because it derives a closed-form
loss from the RL formulation of preference learning, avoiding the
need for a separate reward model + PPO. The key derivation:

Suppose we have preference data: pairs $(x_w, x_l)$ where $x_w$ is
preferred over $x_l$. We model preferences with the **Bradley-Terry**
model:

$$P(x_w \succ x_l) = \frac{\exp(r(x_w))}{\exp(r(x_w)) + \exp(r(x_l))} = \sigma(r(x_w) - r(x_l))$$

where $r$ is some implicit reward. The classical RLHF approach
trains a reward model on this, then optimises a policy
$\pi_\theta$ with KL regularisation against a reference policy:

$$\max_\theta \mathbb{E}\!\left[r(x)\right] - \beta \, \text{KL}(\pi_\theta \,\|\, \pi_\text{ref})$$

DPO's insight: solving the KL-regularised RL problem gives an
analytical optimal policy:

$$\pi^*(x) \propto \pi_\text{ref}(x) \exp(r(x)/\beta)$$

Equivalently:

$$r(x) = \beta \log \frac{\pi^*(x)}{\pi_\text{ref}(x)} + \text{const}.$$

Substituting this expression into the Bradley-Terry preference
model, the constant cancels in the difference and you get a loss
that depends only on $\pi_\theta$ and $\pi_\text{ref}$:

$$\mathcal{L}_\text{DPO}(x_w, x_l) = -\log \sigma\!\left(\beta\!\left[\log \frac{\pi_\theta(x_w)}{\pi_\text{ref}(x_w)} - \log \frac{\pi_\theta(x_l)}{\pi_\text{ref}(x_l)}\right]\right)$$

You can train this directly on preference pairs without a separate
reward model. That's the DPO miracle: convex optimisation on an
analytically-derived loss.

## Why g-DPO instead of plain DPO

For LLMs, preference data is naturally pairwise: a prompt has
multiple completions and humans pick the better one. For
sequence-function regression you have a different structure:

- You have $N$ sequences with continuous fitness values.
- You can form $\binom{N}{2}$ all-against-all pairs, but this is
  wasteful — most pairs are uninformatively different.
- You'd like the *informative* pairs: similar sequences with
  different fitness, so the model learns local structure.

g-DPO solves this by **clustering** sequences into groups of
high-similarity homologs and forming pairs only within each group.
Every pair has small edit distance (at most $\sim 5-10$ residue
differences), so the preference signal is local — the model learns
"changing position 17 from K to R helps" rather than "this whole
clade is generally good".

Sequence similarity within a cluster is typically measured with
either BLOSUM62 alignment scores (module 6) or embedding cosine
similarity (module 12). Cradle reports clustering with embedding
distances; this lets the same evotuned model that generates
proposals also define the cluster geometry, so the system stays
internally consistent.

There's a tension here: smaller clusters give more local pairs but
fewer pairs total. Cradle's hyper-parameter sweet spot (per the
whitepaper hints) is clusters of $\sim 5-10$ sequences with each
sequence appearing in 2-3 clusters.

## The predictor's regression head

A typical predictor head architecture:

```
embeddings (L, d) -> mean pool over L -> Linear(d -> 256) -> ReLU
  -> Linear(256 -> 64) -> ReLU -> Linear(64 -> num_outputs)
```

For the 650M ESM-2 backbone, $d = 1280$, so the head has
$1280 \cdot 256 + 256 \cdot 64 + 64 \cdot K \approx 0.34$M
parameters for $K$ output measurements. Tiny compared to the 650M
backbone.

Two key design choices:

1. **Pooling.** Mean-pool, max-pool, or `<cls>`-token pool? Mean
   tends to win on continuous regression tasks; `<cls>` is more
   common in NLP classification. Per-residue heads (one prediction
   per position) are also possible if the assay has positional
   resolution.
2. **Frozen vs unfrozen backbone.** If you have $\le 1000$
   training examples, freeze the backbone — you don't have enough
   data to safely fine-tune 650M parameters. With $\ge 10000$
   examples, you can safely unfreeze the last few layers. Cradle's
   approach: backbone always frozen during predictor training; the
   logiter (separate model) is the one that gets g-DPO updates.

## Multi-objective heads

Real assays produce multiple measurements per sequence (e.g.
activity, stability, solubility). Three options:

1. **Single head with $K$ outputs.** Simplest; outputs are
   mean-squared-error losses on each. Works fine if the
   measurements are correlated.
2. **Separate heads per measurement.** Heavier but allows
   per-objective hyper-parameter tuning. Recommended when
   measurements have different scales.
3. **Pareto-aware heads.** Output a "score" that already
   incorporates a trade-off between objectives. Used when the
   user already knows the trade-off they want.

Cradle's setup uses option 2 with a downstream **scalarisation**
that combines per-measurement predictions according to user-defined
weights at sampling time.

## Active learning and acquisition functions

The choice of which 96 sequences to test next is an **active
learning** problem. The naive approach — sample whatever the
logiter outputs — wastes plates. Better:

- **Upper confidence bound (UCB):** rank by $\hat{y} + \alpha \cdot \sigma$,
  where $\hat{y}$ is the predictor's mean and $\sigma$ is its
  uncertainty.
- **Expected improvement (EI):** rank by the predicted probability
  of improving over the current best.
- **Thompson sampling:** draw $K$ samples from the posterior over
  $\hat{y}$ and pick the top of each.

For uncertainty estimation, Cradle uses an ensemble of predictor
heads (different random initialisations on the same backbone).
The variance across the ensemble approximates $\sigma$.

Practical detail: in early rounds, when assay data is scarce, the
predictor is unreliable everywhere, so you need a high $\alpha$
(more exploration). As data accumulates, the predictor sharpens
and you reduce $\alpha$ to focus on exploitation.

## Why proteins are different from natural language

LLM post-training has a clean three-step recipe: pretrain on web
text, supervised-fine-tune on instruction-response pairs, RLHF on
preferences. Each step has a clear semantic interpretation.

For proteins, the analogue isn't clean:

- **Pretraining** ✓: UniRef50 is the analogue of "web text".
- **Instruction tuning** ✗: there's no universal instruction
  modality. ESM3's function tokens are an early attempt (module
  14) but they're coarse.
- **Preference learning** ✓ but awkward: assay data is continuous,
  not pairwise; the "preference" concept needs adaptation (g-DPO).

The deeper reason is what von Neumann observed: DNA is "interpreted"
to make proteins, but the "interpreter" (ribosomes, tRNAs,
chaperones, the whole cell) is itself made of proteins. There's
no level above the protein that universally describes its function
in a substrate-independent way. Module 14's discussion of the
esmGFP case study illustrates how ESM3 sidesteps this by
incorporating multiple modalities — sequence, structure, and
function — into a single training objective. Cradle's approach
is more pragmatic: stay in the sequence modality but add an
external "function" channel via the wet-lab assay.

## Forecasting a campaign's success

You typically can't predict a priori whether a Cradle-style
campaign will work. A few signals correlate with success:

1. **Initial template quality.** If the starting protein already
   has measurable activity, optimisation is mostly local. Cold-start
   campaigns (no initial activity) are much harder.
2. **MSA depth.** Proteins with thousands of natural homologs (e.g.
   globins, immunoglobulins) evotune well. Single-sequence outliers
   are tougher because the family signal is weak.
3. **Assay quality.** Low-noise, high-throughput assays are better
   than slow, noisy ones. The predictor's accuracy is bounded by
   the assay's signal-to-noise.
4. **Structural availability.** If you have a crystal structure or
   high-confidence ESMFold prediction, you can use module 21's
   inverse folding as a complementary sampling source. Without
   structure, the pipeline falls back to sequence-only.

Cradle reports successful campaigns when 3-4 of these signals are
favourable. When fewer are, the campaign typically requires more
rounds (or fails outright).

## What's still hard

Even the best 2026-era pipelines struggle with:

- **Long proteins** (> 1000 residues): inference is expensive,
  alignment is unreliable, and per-residue mask heuristics get
  noisier.
- **Multi-domain interfaces**: optimising for the *interface*
  between two domains is much harder than optimising a single
  domain. Both domains need to evolve compatibly.
- **Bound conformations**: PLMs see free-protein sequences, not
  ligand-bound conformers. Improving binding affinity often
  requires structural reasoning the language model can't easily
  provide.
- **Very high-throughput campaigns** (> 10^6 sequences per round):
  the predictor's accuracy ceiling becomes binding; you need
  uncertainty quantification + active learning + robustness to
  long-tail noise to make every plate count.

These are the open research directions the field is actively
working on as of 2026 — multimodal PLMs, structure-conditioned
models, advanced active-learning, and better assay-noise modelling.
There's plenty left to do, and the techniques you've seen in this
course are the foundations on which all of it will be built.
