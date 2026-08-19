# RMSNorm

$$\mathrm{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{d}\sum_{i=1}^{d} x_i^2 + \epsilon}}\odot\gamma$$

Compared to LayerNorm: no mean subtraction, no bias. The empirical finding is that re-centering does not contribute; re-scaling is what stabilizes training. You save one reduction pass and $d$ parameters per norm.

## The fp32 detail

```python
def forward(self, x):
    dtype = x.dtype
    x = x.float()
    x = x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
    return (x.to(dtype)) * self.weight
```

Three things are deliberate here.

**The upcast.** Summing $d$ squared bf16 values accumulates error fast — bf16 has 8 bits of mantissa. Every production implementation computes the statistic in fp32.

**Where the downcast happens.** After the normalization, before the weight multiply. `self.weight` is a parameter in the model dtype; multiplying in fp32 and casting afterwards would give a slightly different result and, more importantly, a different gradient dtype path.

**`rsqrt` rather than dividing by `sqrt`.** One instruction instead of two, and it is the form every kernel uses. Small, but it is the sort of thing that signals you have read real code.

## Where epsilon goes

Inside the square root, added to the mean square. Adding it outside — to the square root's result — changes the behavior for small-magnitude inputs and is a real bug in a few implementations in the wild.

# SwiGLU

$$\mathrm{SwiGLU}(x) = W_{down}\big(\mathrm{Swish}(W_{gate}\,x) \odot W_{up}\,x\big)$$

Three matrices where a standard FFN has two. To hold parameters fixed against a `4d` ReLU FFN's $8d^2$:

$$3 \cdot d \cdot d_{ff} = 8d^2 \implies d_{ff} = \frac{8}{3}d$$

In practice implementations round $\tfrac{8}{3}d$ up to a multiple of 256 for kernel efficiency. Llama-2-7B has $d = 4096$, so $\tfrac{8}{3}d = 10922$, rounded to **11008** — a number worth recognizing, because it appears in every Llama config and looks arbitrary until you know where it comes from.

**Naming, since it trips people up.** The *gate* is the branch that goes through Swish. The *up* projection is the linear branch. They are multiplied elementwise, then the *down* projection returns to $d$. Some codebases name them `w1, w2, w3` in a different order than you expect — always check which one gets the activation.

# RoPE

## The construction

Split the head dimension into pairs of channels. For pair $i$ at position $m$, rotate by angle $m\theta_i$ where

$$\theta_i = \mathrm{base}^{-2i/d_h}, \qquad \mathrm{base} = 10000$$

Low-index pairs rotate fast (short wavelength, local structure); high-index pairs rotate slowly (long wavelength, global position). It is the same geometric frequency ladder as sinusoidal encoding, applied as a rotation rather than an addition.

![Three panels. Left: cosine of the rotation angle against token position for five channel pairs. Middle: wavelength against channel pair index. Right: the rotated dot product against relative offset for three absolute base positions, all coinciding.](/courses/ai-lab-interviews/rope-frequencies.svg)

## Why relativity falls out

A rotation matrix $R_m$ is orthogonal, and $R_m^{\top}R_n = R_{n-m}$. So

$$(R_m q)^{\top}(R_n k) = q^{\top}R_m^{\top}R_n k = q^{\top}R_{n-m}k$$

Absolute position enters the computation; only the difference survives into the score. That single line is the best possible answer to "how does RoPE work" and takes fifteen seconds to say.

## Implementation

```python
# cache, built once
inv_freq = 1.0 / (base ** (torch.arange(0, head_dim, 2) / head_dim))
freqs = torch.outer(torch.arange(seq_len), inv_freq)   # (S, dh/2)
cos, sin = freqs.cos(), freqs.sin()

# applied per forward
x1, x2 = x[..., 0::2], x[..., 1::2]        # interleaved convention
out_even = x1 * cos - x2 * sin
out_odd  = x1 * sin + x2 * cos
```

Details that matter:

- **Q and K only, never V.** Position should determine *which* tokens you attend to, not *what* is retrieved from them. Rotating V is a real bug people ship.
- **After the head split.** Rotation is per head, over the head dimension.
- **Cache the tables.** Recomputing sin and cos every forward pass is pure waste; every implementation precomputes to `max_seq_len`.
- **The two conventions.** *Interleaved* pairs channels $(0,1), (2,3), \dots$; *split-half* pairs $i$ with $i + d_h/2$. Both are valid rotations and both train fine. Mixing them between training and serving produces a model that emits fluent nonsense — a genuinely famous class of production bug.

## Extending context

Because RoPE is a function of position rather than a lookup table, you can change that function after training:

- **Position interpolation.** Divide positions by a factor $s$ so a model trained to 4k covers $4ks$ tokens. Cheap, needs a little continued pretraining, degrades short-context quality slightly.
- **NTK-aware scaling.** Increase the base instead, which stretches low-frequency (long-wavelength) components more than high-frequency ones. Better short-context preservation.
- **YaRN.** Combines the two with per-frequency treatment and an attention temperature correction. The most refined of the extension family.

"How would you extend a 4k model to 32k?" is a very common technical-discussion question. Naming these three, and saying that the fundamental limit is that the model never saw genuinely long-range dependencies during training, is the answer. Worth adding: current models mostly sidestep the problem by pretraining with a much larger base in the first place — Llama 3 uses 500,000 rather than 10,000 — plus a staged long-context training phase, so the extension tricks are now mainly for stretching an existing checkpoint.
