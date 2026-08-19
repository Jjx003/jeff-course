# Scales, zero points, and error

Uniform affine quantization maps real numbers into integers:

$$
q = \operatorname{clip}\left(\operatorname{round}(x/s + z), q_\min, q_\max\right)
$$

and reconstructs with:

$$
\hat{x} = s(q - z)
$$

Here $s$ is the scale and $z$ is the zero point. Symmetric quantization sets
$z=0$ and uses a signed integer range. It is common for weights because it is
simple and hardware-friendly. Asymmetric quantization uses a nonzero zero point
to represent shifted ranges more efficiently, often useful for activations.

## Quantization error

Quantization error is:

$$
e_i = x_i - \hat{x}_i
$$

Common summaries include mean absolute error:

$$
\text{MAE} = \frac{1}{n}\sum_i |x_i - \hat{x}_i|
$$

and mean squared error:

$$
\text{MSE} = \frac{1}{n}\sum_i (x_i - \hat{x}_i)^2
$$

Those summaries are useful but incomplete. A small average error in an
unimportant layer may not matter, while a small-looking error in a sensitive
projection can damage downstream quality. Calibration methods exist because
"minimize local reconstruction error" is not always the same as "preserve model
behavior."

## One number predicts a block's error

Before reaching for calibration, it is worth knowing how far plain rounding
gets you, and the answer is available in closed form.

Take a uniform quantizer with step $\Delta$. If the input varies smoothly on the
scale of $\Delta$ — many distinct values per bin, no mass piled on a single
level — then the rounding error $e = x - \hat{x}$ is approximately uniform on
$[-\Delta/2, \Delta/2]$. That gives the classical **quantizer noise model**:

$$
\mathbb{E}[e] = 0, \qquad
\mathbb{E}[e^2] = \frac{1}{\Delta}\int_{-\Delta/2}^{\Delta/2} e^2\,de
= \frac{\Delta^2}{12}
$$

Now specialize to symmetric absmax INT4 over a group, with codes $-7 \ldots 7$
and $A = \max_i |x_i|$. The step is $\Delta = A/7$, so the noise power is
$A^2/588$. Divide by the signal power $\sigma^2$, where $\sigma$ is the group's
standard deviation, and define the group's **crest factor**

$$
\kappa = \frac{A}{\sigma} = \frac{\max_i |x_i|}{\sigma}
$$

The normalized error of the block collapses to a single quantity:

$$
\frac{\mathbb{E}[e^2]}{\mathbb{E}[x^2]} = \frac{\kappa^2}{588},
\qquad\text{or}\qquad
\text{SQNR} \approx 27.7 - 20\log_{10}\kappa \ \text{dB}
$$

Nothing about the layer, the model, or the task appears in that expression. A
group is hard to quantize exactly to the extent that its largest element dwarfs
its typical element — that is the whole story for plain rounding. The general
$b$-bit form is $\text{SQNR} \approx 6.02b + 4.77 - 20\log_{10}\kappa$ dB, the
familiar "6 dB per bit" rule with a penalty for peakiness.

Here is that prediction against simulation, on a $4096 \times 4096$ Gaussian
weight matrix quantized groupwise:

| Group size $G$ | measured $\kappa$ | predicted $\kappa^2/588$ | measured NMSE |
|---:|---:|---:|---:|
| 32 | 2.41 | 0.0098 | 0.0094 |
| 64 | 2.63 | 0.0117 | 0.0116 |
| 128 | 2.85 | 0.0138 | 0.0138 |
| 256 | 3.05 | 0.0159 | 0.0160 |
| 1024 | 3.45 | 0.0202 | 0.0203 |

Agreement to the third decimal. This is the sense in which quantizing
well-behaved weights is a solved problem: the error is not mysterious, it is
$\kappa^2/588$, and $\kappa$ grows only like $\sqrt{2\ln G}$ because that is how
fast the maximum of $G$ Gaussians grows. Quadrupling the group size costs you
about a decibel and a half.

Which raises the obvious question: if the model is this good, why does the
literature contain so many quantization methods?

## Why group size matters

Groupwise quantization splits a tensor into groups and stores one scale per
group. If a group has $G$ values and each value is stored in 4 bits, the raw
integer payload costs:

$$
4G \text{ bits}
$$

If each group stores a 16-bit scale, the effective cost per value is:

$$
4 + \frac{16}{G} \text{ bits}
$$

That means:

| Group size | Payload bits/value | Scale overhead/value | Total before packing details |
|---|---:|---:|---:|
| 32 | 4 | 0.50 | 4.50 |
| 64 | 4 | 0.25 | 4.25 |
| 128 | 4 | 0.125 | 4.125 |

Small groups adapt better to local ranges but store more metadata. Large groups
have less overhead but more error from outliers. Production formats add packing
constraints, alignment, per-channel scales, codebooks, or nested quantization
of the scales themselves.

## Outliers are the reason the field exists

The answer to the question at the end of the last section is that real weight
and activation tensors are not the clean Gaussians the noise model assumes, and
the deviation is concentrated in a very small number of channels.

Repeat the sweep with 0.5 percent of input channels scaled up by 20×, which is
roughly the pattern reported for OPT- and LLaMA-family activations:

![Normalized INT4 error against group size for clean Gaussian weights and for weights with 0.5 percent outlier channels, alongside effective bits per weight](/courses/model-optimization-systems/quant-group-size-error.svg)

| Group size $G$ | clean NMSE | outlier NMSE | ratio | P(group contains an outlier) |
|---:|---:|---:|---:|---:|
| 32 | 0.0094 | 0.0227 | 2.4× | 0.15 |
| 64 | 0.0116 | 0.0415 | 3.6× | 0.27 |
| 128 | 0.0138 | 0.0771 | 5.6× | 0.47 |
| 1024 | 0.0203 | 0.2685 | 13.2× | 0.99 |

Read the two curves against each other. The clean curve is almost flat — for
well-behaved weights, group size is nearly a free parameter and you should pick
the largest one your accuracy budget tolerates. The outlier curve is steep, and
it is steep for a structural reason: the last column of the table is the
probability that a group of $G$ contiguous channels contains at least one
outlier, $1-(1-p)^G$. Group size controls **containment**. A small group
quarantines an outlier so it damages 32 weights instead of 1024.

That is also where the noise model breaks. At $G=128$ the crest factor is 5.4,
which predicts an NMSE of 0.050, but the measured value is 0.077 — the real
error is more than 1.5× what the model says, and the gap widens with $G$. The
model does not merely lose accuracy here; it errs in the dangerous direction,
*under*-stating the damage. The uniform-error assumption fails
exactly when it matters: once one value forces a wide scale, the small values
in the group no longer spread across bins, they all collapse onto zero, and the
error stops being rounding noise and starts being erasure. A group like

```text
[0.04, 0.02, -0.03, 5.00]
```

has a scale set by 5.00. The three small entries do not get rounded; they get
deleted. Every method in the next three sections is an answer to that specific
failure.

This is why practical methods add structure:

- per-channel scaling gives each output channel its own range;
- groupwise scaling localizes outliers;
- activation-aware methods protect channels that matter for real data;
- mixed precision leaves fragile tensors in higher precision;
- SmoothQuant-style methods redistribute scale between weights and activations.

The three families below are worth understanding at the level of their
objective functions, because their objectives are what differ. The
implementations converge; the questions they ask do not.

## GPTQ: rounding is a least-squares problem

Every method so far minimizes error **on the weights**. That is not the goal.
The goal is to preserve what the layer computes. GPTQ takes that literally and
solves, for a calibration activation matrix $X \in \mathbb{R}^{d_\text{in}
\times n}$,

$$
\hat{W} = \arg\min_{\hat{W}} \; \bigl\lVert WX - \hat{W}X \bigr\rVert_F^2
$$

subject to every entry of $\hat{W}$ lying on the quantization grid. The
objective decouples across output rows, so consider one row $w$ and write
$\delta = w - \hat{w}$. Then

$$
\lVert (w-\hat{w})X \rVert^2 = \delta^\top X X^\top \delta = \delta^\top H \delta,
\qquad H = XX^\top
$$

$H$ is the Hessian of the squared error and it is the same for every row —
it depends only on the calibration data, not on the weights. It is also, in
general, not diagonal: input channels are correlated, so an error introduced in
channel $i$ can be partially *repaired* by adjusting channels $j \ne i$.

That observation is the Optimal Brain Surgeon framework, borrowed from 1990s
pruning. Quantize one coordinate $q$ at a time. Freezing $\hat{w}_q =
\operatorname{quant}(w_q)$ imposes the linear constraint $e_q^\top \delta =
w_q - \operatorname{quant}(w_q)$. Minimizing $\delta^\top H \delta$ subject to
that constraint is a Lagrange problem with a closed-form answer:

$$
\delta^{*} = -\,\frac{w_q - \operatorname{quant}(w_q)}{[H^{-1}]_{qq}}\;
H^{-1}_{:,q},
\qquad
\text{cost} = \frac{\bigl(w_q - \operatorname{quant}(w_q)\bigr)^2}{[H^{-1}]_{qq}}
$$

Read $\delta^{*}$ as: round coordinate $q$, then push the resulting error into
the not-yet-quantized coordinates, weighted by how correlated they are with $q$.
The remaining weights absorb the damage. This is why GPTQ at 4 bits can beat
round-to-nearest at 4 bits without changing the format at all — same bits, same
kernels, better choice of which grid points to land on.

Three engineering decisions turn that into something that runs on a 175B model:

| Problem | GPTQ's answer |
|---|---|
| Greedy ordering needs a fresh $H^{-1}$ per row | Quantize columns in a **fixed** order, so all rows share one $H^{-1}$; at scale this costs almost nothing in accuracy |
| $H$ is often singular or ill-conditioned | Dampen: $H \leftarrow H + \lambda\,\mathrm{diag}(H)$, typically $\lambda \approx 10^{-2}$ |
| Repeated $H^{-1}$ updates are numerically unstable | Precompute a Cholesky factor of $H^{-1}$ and read the needed rows off it |
| Element-at-a-time updates are memory-bound | Apply updates lazily in blocks of ~128 columns |

## AWQ: importance comes from the activations, not the weights

GPTQ asks which rounding minimizes output error. AWQ asks a blunter question
first: *which weights matter at all?* Its central empirical claim is that
salience is determined by the **activation** magnitude of a channel, not the
weight magnitude — keeping the roughly 1 percent of channels with the largest
average $|x_j|$ in FP16 recovers most of the loss, while keeping the 1 percent
with the largest $|w_j|$ recovers almost none.

Mixed precision, though, is miserable for kernels. So AWQ implements protection
without it. For input channel $j$ pick a scale $s_j > 1$ and rewrite

$$
y = \sum_j w_j x_j = \sum_j (w_j s_j)\Bigl(\frac{x_j}{s_j}\Bigr)
$$

which is an exact identity — the $1/s_j$ folds into the preceding layernorm or
projection at no runtime cost. Quantize $w_j s_j$ instead of $w_j$. Since the
absolute step $\Delta$ is set by the group maximum, and scaling up one channel
in a group of 128 barely moves that maximum, the *relative* error on channel $j$
falls by roughly $1/s_j$. You have bought precision for the important channels
and paid for it with a slightly wider group range.

AWQ chooses $s_j = \bar{|x_j|}^{\,\alpha}$ with a single $\alpha \in [0,1]$
found by grid search against layer output MSE. No backpropagation, no
retraining, one hyperparameter per layer.

## SmoothQuant: move the difficulty, do not remove it

AWQ helps weight-only quantization. If you also want low-bit **activations** —
which is what unlocks INT8 or FP8 tensor cores — you face the harder fact that
activation outliers are far more extreme than weight outliers, persist across
tokens in the same channels, and cannot be quantized offline.

SmoothQuant uses the same identity as AWQ, applied per input channel across the
whole matmul:

$$
Y = (X\,\mathrm{diag}(s)^{-1})\cdot(\mathrm{diag}(s)\,W) = \hat{X}\hat{W}
$$

The question is how to choose $s$. Push all the difficulty to the weights
($s_j = \max|X_j|$) and the weights become unquantizable; push it all to the
activations and nothing has changed. SmoothQuant splits it with a migration
strength $\alpha$:

$$
s_j = \frac{\max|X_j|^{\alpha}}{\max|W_j|^{1-\alpha}}
$$

At $\alpha = 1/2$ this has an exact and rather elegant property. The
post-migration maxima become

$$
\max|\hat{X}_j| = \frac{\max|X_j|}{s_j} = \sqrt{\max|X_j|\cdot\max|W_j|},
\qquad
\max|\hat{W}_j| = s_j\max|W_j| = \sqrt{\max|X_j|\cdot\max|W_j|}
$$

They are equal, and both equal the geometric mean of the originals. Half the
difficulty each, in the precise sense that the two tensors now have identical
per-channel dynamic range. Models with unusually severe activation outliers
(GLM-130B is the standard example) want $\alpha \approx 0.75$ instead, pushing
more of the burden onto the weights, which tolerate it better.

![Absolute magnitudes of activations and weights for a linear layer in OPT-13B, before and after SmoothQuant, showing outlier channels migrating from the activation tensor into the weight tensor](/courses/model-optimization-systems/quant-smoothquant-fig4-activation-outliers.png)

*Figure 4 from Xiao et al., SmoothQuant (CC BY 4.0). The leftmost surface is the
original activation tensor: a handful of channels reach magnitude 70 while the
rest sit below 2, and note that the outlier channels are the same across all
300 tokens. That persistence is what makes offline migration possible at all.
The rightmost surface is the weight tensor after absorbing the difficulty —
visibly spikier than the original, still far easier to quantize than the
activations were.*

Three methods, three objectives: GPTQ minimizes layer output error given a
fixed format, AWQ reallocates precision toward channels the data says matter,
SmoothQuant makes activations quantizable at all. They compose, and production
recipes often use more than one.

## INT4 versus NF4

Uniform INT4 places levels evenly. NF4 uses a designed codebook suited to
normally distributed weights. The difference is easiest to describe
geometrically:

![Standard normal density with symmetric INT4 levels below it and NF4 levels below that, showing that NF4 places seven of sixteen levels inside the high-density core while INT4 places only five of fifteen](/courses/model-optimization-systems/quant-int4-vs-nf4.svg)

NF4's levels are not learned. They are constructed from the standard normal
quantile function $\Phi^{-1}$, as midpoints between evenly spaced quantiles:

$$
q_i = \frac{1}{2}\Bigl(\Phi^{-1}(p_i) + \Phi^{-1}(p_{i+1})\Bigr),
\qquad p_i \ \text{evenly spaced in}\ [1-\delta,\ \delta]
$$

then rescaled so the outermost levels sit at $\pm 1$. Two details in that
construction are load-bearing. The offset $\delta$ keeps $\Phi^{-1}$ away from
its infinite tails. And the 16 levels are split asymmetrically — 8 negative,
plus zero, plus 7 positive — specifically so that **zero is exactly
representable**. Without that, every padded position and every genuinely-zero
weight would acquire a small bias, which accumulates across 80 layers.

It is worth being precise about what NF4 optimizes, because the phrase
"information-theoretically optimal" gets repeated loosely. Quantile
quantization gives every code point equal probability mass under the assumed
$\mathcal{N}(0,1)$, which maximizes the entropy of the code distribution — no
code is wasted. That is *not* the same as minimizing MSE. The MSE-optimal
16-level codebook for a Gaussian is the Lloyd–Max quantizer, whose levels are
conditional means of their bins, and it differs from NF4. NF4 optimizes code
utilization; Lloyd–Max optimizes reconstruction error. For frozen pretrained
weights the two are close enough that the simpler, data-independent
construction wins.

The assumption is doing real work here, and it is worth checking rather than
inheriting. NF4 is built for zero-mean Gaussian data. A tensor that is skewed,
bimodal, or already sparsified is not that, and on such a tensor NF4's careful
level placement is spent in the wrong place. This is also why NF4 appears
overwhelmingly on frozen base weights and rarely on activations or KV entries:
pretrained weight blocks really are close to Gaussian, and the things produced
at runtime are not.

| Format | Level placement | Zero exact? | Good fit |
|---|---|---|---|
| INT4 (symmetric) | evenly spaced after scaling | yes (code 0) | hardware-friendly, one code wasted |
| NF4 | denser near common normal values | yes, by construction | frozen pretrained weights in QLoRA |
| Lloyd–Max | MSE-optimal bin centroids | only if imposed | reference point, rarely deployed |

NF4 still needs scales and dequantization. It is not magic; it is a better
allocation of 16 code points for a distribution that pretrained weights happen
to have.

## Weight-only versus weight-activation quantization

Weight-only quantization stores weights in low-bit form and dequantizes them
during computation, often accumulating in FP16/BF16/FP32. It mainly reduces
model storage and weight bandwidth. It is attractive for decode when reading
weights dominates.

Weight-activation quantization uses low-bit activations too. This can unlock
faster low-bit matmuls on supported hardware, but it is harder because
activation ranges depend on inputs. Calibration must see representative data,
and online scaling may add overhead.

## KV cache is its own problem

KV-cache quantization has a different lifecycle. Weights are fixed after model
loading. KV entries are produced during each request. That makes cache
quantization both attractive and delicate:

- attractive because long context and many users create huge cache pressure;
- delicate because quantization happens on the serving path;
- workload-dependent because prompt distributions affect ranges;
- quality-sensitive because attention repeatedly uses cached values.

Some systems quantize only older cache blocks, some quantize per head or per
token block, and some keep special tokens or layers at higher precision. The
right design depends on latency, context length, and accuracy tolerance.

## Accuracy is workload-specific

A chat benchmark, a code benchmark, a long-context retrieval benchmark, and a
protein variant-effect benchmark may react differently to the same bit width.
Treat quantization as an engineering experiment, not a universal truth.

Useful evaluation pairs include:

| Deployment goal | Quality check |
|---|---|
| chat serving | preference, safety, refusal, tool-use behavior |
| code generation | unit tests, pass@k, repository-level tasks |
| retrieval over long context | needle retrieval, citation accuracy |
| protein embeddings | downstream classification or regression |
| folding pipeline | structure metrics and confidence calibration |

## Transition

The next module strips all of this down to the core mechanism and then puts it
under load: split a real weight matrix into groups, choose a symmetric scale per
group, pack signed 4-bit codes two per byte, reconstruct, and measure the error
at the layer's output rather than on the weight. The same sweep runs twice, once
on well-behaved weights and once with outlier channels, because the answer to
"what group size should I use" is different in those two worlds.

## Going deeper

The primary sources for the three method families derived above, plus the
formats they target:

- GPTQ, accurate post-training quantization for generative transformers: https://arxiv.org/abs/2210.17323
- Optimal Brain Surgeon, the 1993 origin of the second-order update: https://proceedings.neurips.cc/paper/1992/hash/303ed4c69846ab36c2904d3ba8573050-Abstract.html
- AWQ, activation-aware weight quantization: https://arxiv.org/abs/2306.00978
- SmoothQuant, migrating quantization difficulty: https://arxiv.org/abs/2211.10438
- LLM.int8() and the discovery of emergent activation outliers: https://arxiv.org/abs/2208.07339
- QLoRA, which introduces NF4 and double quantization: https://arxiv.org/abs/2305.14314
- KIVI, asymmetric 2-bit KV cache quantization: https://arxiv.org/abs/2402.02750
- NVIDIA TensorRT-LLM quantization recipes: https://nvidia.github.io/TensorRT-LLM/latest/features/quantization.html

The figure comparing group sizes on clean and outlier-contaminated weights is
regenerated by `tools/course-figures/model_optimization_figures.py`; the
simulation is short enough to read, and worth reading before trusting the
numbers quoted here.
