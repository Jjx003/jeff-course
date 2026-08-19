# Rapid-Fire Answers

**"What is the Chinchilla result?"**
> At fixed training compute, parameters and tokens should scale equally, roughly 20 tokens per parameter. Chinchilla at 70B on 1.4T tokens beat Gopher at 280B on 300B tokens at the same compute. Kaplan had said to scale the model faster; the difference came down to tuning the learning-rate schedule per run rather than fixing it across sizes.

**"You have $10^{23}$ FLOPs. What do you train?"**
> Compute-optimal is $N = \sqrt{C/120} \approx 29$B on about 580B tokens. But if this is a model I will serve, I would train smaller and longer — maybe 8B on 2T — because the inference cost dominates over the model's lifetime.

**"Why is there an irreducible loss term?"**
> Natural text has entropy. Even a perfect model of the distribution cannot predict the next token better than the distribution allows. $E \approx 1.69$ nats in the Chinchilla fit.

**"How would you decide whether a new architecture is worth training at scale?"**
> Train a ladder of small models under both conditions, fit scaling laws to each, and compare the fitted curves rather than individual points. That catches interventions whose benefit shrinks with scale, which a single small-scale A/B cannot. I would be explicit that extrapolating more than an order of magnitude is speculative, and that the ladder is only valid if hyperparameters are tuned at every rung.

**"Are we running out of data?"**
> For the highest-quality web text, plausibly. Repetition holds up for about 4 epochs and then degrades. The active responses are synthetic data, multimodal data, and spending compute at inference time instead of on more pretraining tokens.

# Traps

- **Quoting "20 tokens per parameter" as if it were a deployment rule.** It is a training-compute-optimal rule. Say which cost you are optimizing.
- **Saying Kaplan was "wrong".** Most of Kaplan's findings hold. One conclusion was distorted by a hyperparameter protocol issue — that is a more accurate and more interesting answer.
- **Treating scaling laws as predicting capability.** They predict loss. The map from loss to benchmark performance is monotone but not smooth.
- **Forgetting that data quality moves the curve.** "How many tokens" is incomplete without "of what".

# Further Reading

- [Scaling Laws for Neural Language Models](https://arxiv.org/abs/2001.08361) — Kaplan et al., 2020.
- [Training Compute-Optimal Large Language Models](https://arxiv.org/abs/2203.15556) — Hoffmann et al., 2022. The Chinchilla paper; the isoFLOP figures are worth looking at directly.
- [Beyond Chinchilla-Optimal](https://arxiv.org/abs/2401.00448) — accounting for inference cost in the optimization.
- [Scaling Data-Constrained Language Models](https://arxiv.org/abs/2305.16264) — where the 4-epoch repetition finding comes from.
