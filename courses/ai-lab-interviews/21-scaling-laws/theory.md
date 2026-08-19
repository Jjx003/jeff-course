# Kaplan (2020)

The first systematic study. Findings that survived:

- Loss follows a **power law** in model size, dataset size, and compute, over many orders of magnitude.
- **Architecture details matter far less than scale.** Width versus depth, and most hyperparameters, are second-order compared to $N$, $D$, and $C$.
- Larger models are **more sample-efficient** — they reach a given loss in fewer tokens.

The conclusion that did not survive: given more compute, scale the model much faster than the data. Kaplan's recommendation implied roughly $N \propto C^{0.73}$ and $D \propto C^{0.27}$.

**Why it was wrong.** Hoffmann et al. attributed it primarily to Kaplan's use of a fixed learning-rate schedule across model sizes rather than one tuned to each run's token count, which systematically under-trained the smaller models and made model size look more valuable than data. Later analyses add two more contributors: Kaplan fitted on *non-embedding* parameter counts, which distorts the fit badly at the small end of his range, and his model-size sweep was narrow. The lesson generalizes regardless: a scaling law is only as trustworthy as the hyperparameter protocol behind it, and "did you tune the schedule per run?" is a legitimate question to ask of any scaling claim.

The models built on Kaplan's advice — GPT-3 at 175B on 300B tokens, Gopher at 280B on 300B — were all substantially under-trained.

# Chinchilla (2022)

Hoffmann et al. redid it with per-run schedules and three independent methods:

1. **Fix model size, vary tokens.** Read the compute-optimal point off each training curve.
2. **IsoFLOP profiles.** Fix compute, sweep model size, find the minimum. This is the left panel of the figure above.
3. **Fit the parametric form** $L(N,D)$ directly and minimize analytically.

All three agreed: $N$ and $D$ should scale **equally**, at roughly $C^{0.5}$ each. In practical terms, about **20 tokens per parameter**.

The demonstration was Chinchilla — 70B on 1.4T tokens — beating Gopher (280B on 300B tokens) across the board at the same training compute. A 4x smaller model, better results, and vastly cheaper to serve.

## Doing the arithmetic

Given a budget $C$:

$$N_{opt} \approx \sqrt{\frac{C}{6\times20}}, \qquad D_{opt} \approx 20 N_{opt}$$

For $C = 10^{23}$: $N \approx \sqrt{10^{23}/120} \approx 2.9\times10^{10}$, so about a 29B model on 580B tokens. Being able to run that in your head is a genuinely useful interview skill.

# Why Deployed Models Ignore This

Chinchilla optimizes **training** compute. It ignores inference entirely.

Consider two models that are both good enough for the product you are shipping:
- A: 70B, trained compute-optimally on 1.4T tokens.
- B: 7B, trained on 2T tokens — far past compute-optimal, so a worse loss per unit of training compute, and a genuinely worse model than A, but above your quality bar.

B costs more to train per unit of quality, and **10x less per token to serve**. If you will serve a trillion tokens, the training difference is a rounding error and the serving difference is the entire budget. The decision is not "which is better" but "how much quality am I willing to trade for a 10x serving cost", and past a certain scale the answer is usually "quite a lot".

This is the "inference-optimal" or "over-training" regime, and it is where nearly every deployed model now sits. Llama-3-8B saw 15T tokens — roughly 1875 tokens per parameter, about 90x past Chinchilla.

**The honest limitation:** returns do diminish. The $B/D^{\beta}$ term flattens, so each additional trillion tokens buys less. There is a point where more data stops being worth the training cost even accounting for inference savings, and finding it is an empirical question rather than a formula.

# Using Scaling Laws to Decide Things

This is the part interviewers care about most, because it is the part that is actually a research skill.

**The workflow:**

1. Train a ladder of small models — say 50M, 100M, 300M, 1B — under the intervention you are evaluating and under the baseline.
2. Fit a scaling law to each.
3. Compare the *fitted curves*, not the individual points.
4. Extrapolate to the target scale, and be explicit about how far you are extrapolating.

**What this catches that a single small-scale comparison does not:** interventions whose benefit shrinks with scale. Many architecture tweaks help a 100M model and do nothing at 10B, because they are compensating for a capacity limitation that scale removes anyway. A single small-scale A/B cannot distinguish "this helps" from "this helps small models".

**The honest caveats to volunteer:**

- Extrapolating more than ~1 order of magnitude beyond your largest fitted point is speculative.
- The fit assumes your hyperparameters are properly tuned at every ladder rung — which is exactly what Kaplan got wrong.
- Scaling laws predict *loss*, not downstream capability. The relationship between the two is monotone but bumpy, and emergent-looking jumps in benchmark scores often reflect the metric's discreteness rather than the model's.

# What Breaks Scaling Laws

**Data repetition.** Up to about 4 epochs, repeated data is nearly as good as fresh data. Past that, returns collapse and eventually go negative. This matters because high-quality text is finite.

**Data quality.** Curation shifts the whole curve. A well-filtered corpus reaches a given loss with substantially fewer tokens, which means "how many tokens" is not a well-posed question without "of what".

**Architecture changes that alter the constants.** MoE has its own scaling law in terms of *active* parameters. Retrieval augmentation changes what the model needs to store.

**Post-training.** Scaling laws describe pretraining loss. RLHF, instruction tuning, and reasoning-focused RL change capability substantially at fixed pretraining compute — and test-time compute (spending more tokens thinking at generation time) is a different axis entirely, with its own scaling curves. Since the o1/R1 generation, labs treat "pretrain more" versus "RL more" versus "think longer at inference" as a three-way allocation problem, which is a genuinely different world from the one Chinchilla optimized in.

**Distillation.** The train-big, serve-small pattern changes the deployment calculus once more: a compute-optimal large model becomes a teacher, and what ships is a distilled student that beats any same-size model trained from scratch on the same budget. Several frontier families now work this way, which is one more reason the parameter counts you can serve are decoupled from the compute that produced them.
