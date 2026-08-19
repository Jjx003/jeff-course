# Theory notes: the arithmetic of sharding

## 1. Ring all-reduce, derived

An all-reduce computes the elementwise sum of a length-$n$ buffer held on each
of $p$ GPUs and leaves the full sum on all of them. The ring algorithm does it
in two phases.

**Reduce-scatter.** Divide the buffer into $p$ chunks. In each of $p-1$ steps,
every GPU sends one chunk (of size $n/p$) to its right neighbor and receives
one from its left, adding what it receives into its local copy. After $p-1$
steps, each GPU holds the *complete sum* of exactly one chunk.

**All-gather.** Another $p-1$ steps circulate the finished chunks so every GPU
ends with all of them.

Each GPU therefore sends $2(p-1)$ chunks of $n/p$ bytes:

$$
\text{bytes per GPU} = \frac{2(p-1)}{p}\,n
\qquad
t_\text{ring} = 2(p-1)\,\alpha + \frac{2(p-1)}{p}\cdot\frac{n}{\beta_\text{link}}
$$

Two things follow immediately. The bandwidth term is essentially independent of
$p$ — the factor $2(p-1)/p$ climbs from 1 at $p=2$ toward an asymptote of 2 —
which is why ring all-reduce is called "bandwidth-optimal." The latency term is
*linear* in $p$, which is why rings are the wrong algorithm for small messages.
For those, NCCL switches to tree or one-shot algorithms with $O(\log p)$ or
$O(1)$ depth; the practical consequence for decode is that a 16 KB all-reduce
across 8 NVLink-connected GPUs costs a roughly fixed 5–15 µs, dominated by
launch and synchronization rather than by wire time. The 10 µs figure the
reading uses is a representative measured value, not a law; measure your own
fabric, and expect InfiniBand to be several times worse.

## 2. Why exactly two all-reduces per layer

Write the MLP as $Y = \sigma(XA)B$ with $A$ column-sharded and $B$ row-sharded.
GPU $i$ computes

$$
Y^{(i)} = \sigma(XA_i)\,B^{(i)}, \qquad Y = \sum_{i=1}^{p} Y^{(i)}
$$

The identity holds because the column shard of $A$ produces exactly the rows of
$\sigma(\cdot)$ that the row shard of $B$ consumes; the elementwise $\sigma$
never mixes columns, so it commutes with the sharding. One all-reduce.

Attention is the same composition wearing different clothes: the QKV
projections are column-sharded (heads are just named groups of columns), the
per-head attention never mixes heads, and the output projection is row-sharded.
One all-reduce.

What *cannot* be sharded away is anything that mixes the full hidden dimension
per token: RMSNorm needs the complete hidden vector to compute its scale, and
the residual stream must be whole where the norm reads it. That is why the
all-reduces sit where they sit — each one lands immediately before a norm. The
refinement called **sequence parallelism** (Korthikanti et al., 2022) notices
that norms are pointwise *along the sequence*, so the norm's input can be
sharded by token position instead: the all-reduce splits into a reduce-scatter
before the norm and an all-gather after it. Same total bytes ($2(p-1)n/p$
each way), but the activations between them are $p\times$ smaller — a memory
optimization for prefill and training, not a decode-latency one.

The wrong cut is worth stating algebraically because the coding module measures
it. If you row-shard $A$ instead, each GPU holds a partial sum $X^{(i)}A^{(i)}$
of the *pre-activation*, and

$$
\sum_i \sigma\!\left(X^{(i)}A^{(i)}\right) \ne
\sigma\!\left(\textstyle\sum_i X^{(i)}A^{(i)}\right)
$$

for any nonlinear $\sigma$. Fixing it requires an all-reduce *before* the
nonlinearity — doubling the collectives per block — which is precisely the cost
the column-then-row ordering is designed to avoid.

## 3. TP decode floors with real constants

Model: 70B parameters, BF16, H100 SXM (3.35 TB/s HBM each), 80 layers, two
all-reduces per layer at a fixed $\alpha_\text{eff} = 10$ µs, bandwidth term
negligible at batch 1.

$$
t_\text{step}(p) = \frac{140\ \text{GB}}{p \times 3.35\ \text{TB/s}}
+ 160\,\alpha_\text{eff}\,[p > 1]
$$

| TP | weights/GPU | memory floor | collectives | step floor | speedup | efficiency |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 140 GB (does not fit) | 41.79 ms | — | 41.79 ms | 1.0× | 100% |
| 2 | 70 GB | 20.90 ms | 1.6 ms | 22.50 ms | 1.86× | 93% |
| 4 | 35 GB | 10.45 ms | 1.6 ms | 12.05 ms | 3.47× | 87% |
| 8 | 17.5 GB | 5.22 ms | 1.6 ms | 6.82 ms | 6.13× | 77% |

The trend is the whole argument: the parallelizable term halves while the
collective term stands still. Extrapolating to TP 16 across two nodes would
put the memory floor at 2.6 ms against a collective term that has *grown*
(InfiniBand $\alpha$ is worse), and the marginal GPU buys almost nothing —
before even accounting for the KV-head replication in §5.

A subtlety in row 1: TP 1 cannot actually run this model, so "1.0×" is a
bookkeeping baseline, not an option. The honest comparison for a capacity-bound
model is TP 8 versus TP 2 with INT4 weights (35 GB fits on one GPU pair), and
quantization's 4× byte reduction competes directly with adding silicon. That
competition — bits versus GPUs — is a genuine deployment decision, and the
course's quantization modules are half of its input.

## 4. The pipeline bubble, derived

GPipe-style schedule: $p$ stages, $m$ microbatches, each taking one unit per
stage. Microbatch $j$ enters stage $i$ at time $i + j$ (zero-indexed), so the
last microbatch leaves the last stage at time $(p-1) + (m-1) + 1 = m + p - 1$.
Useful work fills $m$ units on each stage. The idle fraction on the machine is

$$
\text{bubble} = \frac{(m+p-1) - m}{m+p-1} = \frac{p-1}{m+p-1}
$$

At $m = p$: bubble $= (p-1)/(2p-1) \approx 50\%$ for large $p$. At $m = 4p$ it
is about 19 percent; at $m = 8p$, 11 percent. Interleaved schedules (each GPU
holds several non-contiguous stage slices) divide the bubble further at the
cost of more frequent communication.

For *decode serving* specifically, the microbatches are different requests'
tokens, and the bubble argument becomes an admission-control argument: a PP
deployment only earns its keep at concurrency well above the stage count. If
your traffic gives the scheduler 4 concurrent requests on an 8-stage pipeline,
most of the machine is idle most of the time and TP-with-fewer-GPUs would beat
it. Module 12's continuous batching is what supplies the concurrency PP needs.

## 5. TP and the KV cache: the GQA ceiling

Per-GPU KV cache for a model with $H_{kv}$ KV heads under TP $p$:

$$
\text{cache per GPU} =
\frac{\text{total cache}}{\min(p, H_{kv})}
\times
\underbrace{\left[\text{replication} = \frac{p}{\min(p,H_{kv})}\right]}_{\text{when } p > H_{kv}}
$$

| TP | KV heads/GPU (of 8) | cache scaling | note |
|---:|---:|---:|---|
| 2 | 4 | 1/2 | clean |
| 4 | 2 | 1/4 | clean |
| 8 | 1 | 1/8 | standard 70B deployment |
| 16 | 1 (replicated) | 1/8 | weights halve again, cache does not |

The row that bites is the last one. Past $p = H_{kv}$, the marginal GPU brings
HBM for weights but not for cache, and module 11 showed that at serving batch
sizes the cache is the larger tenant. Designers choose $H_{kv} = 8$ partly
*because* it matches the 8-GPU node — GQA is simultaneously a bandwidth
optimization (module 11's $2H_q/(H_{kv}b)$ intensity) and a statement about the
largest TP degree the model expects to meet.

Head-count divisibility is the same constraint in miniature: TP degree must
divide $H_q$ (64 here), which is why you see TP 2/4/8 and never TP 6.

## 6. MoE: the union bound and the straggler

**Distinct experts touched.** Each of $B$ tokens picks $k$ of $E$ experts.
Under uniform independent routing, a given expert is missed by one token with
probability $1 - k/E$, so

$$
m(B) = \mathbb{E}[\text{distinct experts}] = E\left(1 - \left(1 - \frac{k}{E}\right)^B\right)
$$

This is the coupon-collector curve: linear ($m \approx Bk$) while the batch is
small, saturating at $E$ once $B \gtrsim E/k \cdot \ln E$. The two regimes are
the two claims in the reading: batch-1 decode reads $k$ experts (active-param
traffic), large-batch decode reads all $E$ (total-param traffic) while only
doing active-param FLOPs, and the intensity ratio to dense is $k/E$ in the
limit.

Real routers are trained toward balance but are not uniform; correlated routing
(many tokens in a batch choosing the same expert) makes $m(B)$ *smaller* —
better for bandwidth, worse for the straggler below. The formula is a model,
and like the roofline it is a first question, not a prediction.

**The straggler.** Under EP, expert loads are multinomial: expert $e$ receives
$n_e$ tokens with $\mathbb{E}[n_e] = Bk/E$. The all-to-all and the expert
matmuls complete when the most-loaded rank completes, so the slowdown is
$\max_e n_e / (Bk/E)$. For balanced random routing the max exceeds the mean by
a factor $1 + O(\sqrt{E \ln E / (Bk)})$ — small for huge batches, brutal for
small ones. With 256 experts, $k=8$, and 1,024 tokens, the mean load is 32
tokens per expert and the expected max is around 50 — a 1.6× tax on the whole
layer. This is why serving stacks cap per-expert tokens (capacity factor),
replicate hot experts, or reshuffle expert placement against measured traffic,
and why "MoE has $1/E$ the FLOPs" never turns into $E\times$ the throughput.

**Shared parameters are dense.** Attention, embeddings, and any shared expert
follow module 1's original arithmetic unchanged. A "sparse" model is a dense
model with a sparse MLP bolted on, and its roofline is the weighted mix of the
two derivations. DeepSeek-V3's shared expert exists partly to keep some of
every token's FLOPs on weights that batching *can* amortize.

## 7. What did not make this module

Fully sharded data parallelism, ZeRO, and gradient collectives are training
machinery; they matter enormously and belong to a training-systems course.
Context/ring-attention parallelism — sharding one very long sequence's KV
across GPUs and passing blocks around during attention — is the inference-side
technique this module skips; it inherits everything from module 11's decode
intensity analysis with the link bandwidth substituted for HBM bandwidth, which
is exactly why it is a last resort. Disaggregated prefill (module 11's theory
notes) composes with everything here: prefill fleets favor TP for time-to-first-
token, decode fleets stack PP for capacity, and the KV cache migrates between
them over the same fabric the collectives use.
