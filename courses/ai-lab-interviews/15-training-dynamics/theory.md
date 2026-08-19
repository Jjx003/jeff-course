# AdamW

## The update

$$m_t = \beta_1 m_{t-1} + (1-\beta_1)g_t$$

$$v_t = \beta_2 v_{t-1} + (1-\beta_2)g_t^2$$

$$\hat{m}_t = \frac{m_t}{1-\beta_1^t}, \qquad \hat{v}_t = \frac{v_t}{1-\beta_2^t}$$

$$\theta_t = \theta_{t-1} - \eta\lambda\theta_{t-1} - \eta\frac{\hat{m}_t}{\sqrt{\hat{v}_t}+\epsilon}$$

Defaults: $\beta_1 = 0.9$, $\beta_2 = 0.95$ for LLMs (0.999 elsewhere), $\epsilon = 10^{-8}$, $\lambda = 0.1$.

## What each moment does

**First moment $m$** — a running mean of gradients. If gradients have pointed consistently in one direction, the optimizer moves more confidently that way; it accumulates velocity and barrels through noise.

**Second moment $v$** — a running mean of *squared* gradients. Dividing by $\sqrt{v}$ gives each parameter its own effective step size: consistently large gradients take smaller steps. It normalizes every parameter onto the same scale, which is what makes Adam robust to the wildly different gradient magnitudes across a transformer's layers.

## Bias correction

$m$ and $v$ both initialize at zero, so early estimates are biased toward zero. At $t=1$ with $\beta_2 = 0.999$:

$$v_1 = 0.001 g_1^2$$

which is about 1000x too small, so $\sqrt{v_1}$ is ~32x too small — but $m_1$ is only 10x too small, leaving a first step about 3.2x too large. Dividing by $1-\beta_2^t$ corrects exactly this — and note the correction decays to nothing, since $\beta^t \to 0$.

**This is why warmup exists.** Bias correction fixes the *expected* magnitude, but early $v$ is still estimated from a handful of samples and is therefore noisy. A parameter that happened to see small gradients for a few steps gets an enormous update. Warmup keeps the learning rate small while the estimates stabilize.

## Adam versus AdamW

In Adam, "weight decay" is implemented as L2 regularization added to the gradient:

$$g_t \leftarrow g_t + \lambda\theta$$

That term then passes through the $\sqrt{v}$ normalization, so a parameter with large gradients — and therefore large $v$ — gets *less* decay. The regularization strength ends up coupled to gradient magnitude, which is not what anyone wanted.

AdamW decouples it, applying $-\eta\lambda\theta$ directly to the parameter, outside the adaptive scaling. Every parameter is decayed at the same relative rate.

**The follow-up:** which parameters get weight decay? Convention is matrices yes, biases and norm gains no. Decaying a norm's scale toward zero shrinks the activations it is meant to normalize, which is counterproductive. Handling this means parameter groups:

```python
torch.optim.AdamW([
    {"params": decay_params,    "weight_decay": 0.1},
    {"params": no_decay_params, "weight_decay": 0.0},
])
```

## Memory

Per parameter: the parameter, its gradient, $m$, and $v$. In fp32 that is 16 bytes, so optimizer state alone is 8 bytes per parameter — half of everything. That is why 8-bit Adam and ZeRO stage 1 exist, and why "shard the optimizer state first" is the standard first move in distributed training.

## Beyond AdamW: Muon

AdamW is still the default answer, but the first credible challenger in a decade is worth knowing in 2026. **Muon** takes the momentum-SGD update for a weight *matrix* and orthogonalizes it (approximately, via a few Newton–Schulz iterations) before applying it — the idea being that a matrix update's useful content is its direction in matrix space, not its per-element magnitudes. Three things to be able to say about it:

- It applies only to 2-D hidden weight matrices; embeddings, the output head, norms, and biases stay on AdamW.
- It keeps one momentum buffer instead of two moments — half of Adam's optimizer state.
- It has been validated at frontier scale: Moonshot AI trained Kimi K2 (a ~1T-parameter MoE) with a Muon variant, adding QK-clip to control the attention-logit growth that showed up at scale.

Being able to say *why* it is plausible — orthogonalization equalizes the update's effect across directions the way Adam's $\sqrt{v}$ equalizes it across coordinates — marks you as current without overclaiming.

![Two panels. Left: singular values of a raw momentum update on a log scale, dropping sharply after the first few, against the same matrix after five Newton-Schulz steps, which stays nearly flat. Right: cumulative share of update energy against number of directions kept, where the raw update reaches half its energy in two of 128 directions and the orthogonalized one climbs evenly.](/courses/ai-lab-interviews/muon-orthogonalization.svg)

## The distinguishing question

> "How do you decide whether something belongs in the optimizer or the learning-rate schedule?"

If it depends on the step count alone, it is a schedule. If it needs per-parameter history, it is the optimizer. That single sentence resolves the whole design question and is a satisfying thing to have ready.

# Learning-Rate Schedules

## Warmup

Linear from 0 to peak over roughly 0.1–1% of total steps — typically 2000 steps for a large run.

Warmup prevents a specific failure: early in training, $v$ is a poor estimate, so a full-size step can be enormous for some parameters. It also reduces the "primacy effect" of the first few batches, which would otherwise pull the model a long way in a direction determined by a tiny sample.

## Cosine decay

$$\eta_t = \eta_{min} + \frac{1}{2}(\eta_{max}-\eta_{min})\left(1+\cos\frac{\pi t}{T}\right)$$

typically decaying to 10% of peak. Empirically strong, and the default for most of the last several years.

**Its real problem:** you must fix $T$ before you start. Train longer than planned and the schedule is wrong; stop early and you get a model that never had its decay phase, which is measurably worse than a properly-annealed model at the same token count.

## Warmup-stable-decay

Warmup, then hold at peak indefinitely, then a short sharp decay (last 10–20% of steps) when you decide to stop.

This decouples the schedule from a total step count. You can branch a checkpoint from the stable phase at any point and anneal it into a finished model, which makes continued pretraining and data-mixture experiments dramatically cheaper. It is increasingly the default at frontier labs, and knowing *why* — the flexibility, not the loss curve — is the answer that lands.

## Batch size and learning rate

The relationship people expect you to know:

- **Linear scaling** ($\eta \propto B$) is the SGD rule and holds for moderate batch sizes.
- **Square-root scaling** ($\eta \propto \sqrt{B}$) is the better rule of thumb for Adam, because the second moment already normalizes gradient magnitude.
- **Critical batch size**: beyond some point, larger batches stop improving gradient quality and only cost compute. It grows as training progresses, which is why batch-size ramps exist.

# Initialization

Standard practice for LLMs: normal with $\sigma = 0.02$, with residual-output projections scaled by $1/\sqrt{2L}$.

The classical results are worth being able to state:

- **Xavier/Glorot:** $\mathrm{Var}(W) = 2/(n_{in}+n_{out})$, derived to preserve activation variance in both directions for symmetric activations.
- **He/Kaiming:** $\mathrm{Var}(W) = 2/n_{in}$. The factor of 2 compensates for ReLU zeroing roughly half the units.

μP (maximal update parameterization) is the modern refinement: parameterize initialization and learning rates so that the *optimal* hyperparameters are invariant to width. That lets you tune on a small model and transfer to a large one — extremely valuable when one run costs millions of dollars, and a strong thing to be able to name when asked "how would you pick a learning rate for a model 10x bigger?"

# Failure Modes

## Loss spikes

The signature failure of large-scale training: a sudden jump in loss, sometimes recovering, sometimes not.

**Causes, in rough order of likelihood:**

1. A bad batch — corrupted data, a pathological repetition, a very long document.
2. Attention logit growth, where logits drift large enough to saturate softmax. QK-norm was introduced for exactly this.
3. An unlucky interaction between a large gradient and stale second-moment estimates.

**Mitigations:** gradient clipping (near-universal), QK-norm, skipping batches whose gradient norm exceeds a threshold, and — the practical one — keeping frequent checkpoints so you can roll back and skip the offending data.

## Divergence

Loss goes to NaN or infinity and never recovers. Learning rate too high, an fp16 overflow (bf16 largely fixed this), or a numerically unstable op. Print the gradient norm every step: a spike immediately before the NaN tells you it was the update; a NaN with no spike points at a forward-pass instability.

## Gradient clipping

Compute the global norm across all parameters. If it exceeds a threshold — 1.0 is the near-universal choice — scale every gradient down by the same factor.

Global, not per-parameter: clipping each tensor separately would change the *direction* of the update, whereas global clipping preserves direction and only bounds the magnitude. That distinction is a common follow-up.

The gradient-norm trace is also the single most useful diagnostic plot in a training run. A healthy run has a slowly declining, low-variance norm. Spikes precede loss spikes; a sudden collapse to zero means something upstream broke.
