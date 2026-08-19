# Parameter count and memory

For a dense matrix:

$$
\text{params}(W) = d_\text{out}d_\text{in}
$$

For a LoRA adapter:

$$
\text{params}(\text{LoRA}) = r(d_\text{in} + d_\text{out})
$$

The ratio is:

$$
\frac{r(d_\text{in}+d_\text{out})}{d_\text{in}d_\text{out}}
$$

For a square matrix with $d_\text{in}=d_\text{out}=d$, this simplifies to:

$$
\frac{2r}{d}
$$

So with $d=4096$ and $r=16$:

$$
\frac{2 \times 16}{4096} \approx 0.0078
$$

or about 0.78 percent of the dense matrix's parameter count.

## Where adapters are inserted

LoRA is usually applied to selected linear projections, such as:

| Transformer component | Why adapt it? |
|---|---|
| query projection | changes what the model attends to |
| value projection | changes what information is carried forward |
| output projection | changes how attention results mix |
| MLP up/down projections | changes feature transformations |

Adapting more matrices increases capacity and memory. Adapting fewer matrices
is cheaper and may be enough for narrow tasks. Rank, target modules, alpha, and
dropout are all part of the adapter design.

## Initialization is a correctness requirement, not a heuristic

LoRA initializes $A \sim \mathcal{N}(0,\sigma^2)$ and $B = 0$. The zero is not
a tuning choice. It guarantees

$$
W' = W + \frac{\alpha}{r}BA = W \quad\text{at step 0}
$$

so training begins from exactly the pretrained function. Initialize both
randomly and you have silently perturbed every layer before the first gradient
step, discarding part of what you paid to pretrain. One of the two factors must
be zero; which one is a weaker convention, since either choice leaves a nonzero
gradient for the other and breaks symmetry.

## Why $\alpha/r$, and why some people use $\alpha/\sqrt{r}$

The original paper motivates the $\alpha/r$ scaling as reducing the need to
retune the learning rate when $r$ changes. That motivation is worth checking,
because a variance argument gives a different answer.

Take $A \in \mathbb{R}^{r \times d_\text{in}}$ and $B \in \mathbb{R}^{d_\text{out}
\times r}$ with entries that are roughly zero-mean and independent — true in
mid-training, though not at step 0 where $B=0$. Propagate variances through the
two matmuls:

$$
\operatorname{Var}\bigl[(Ax)_k\bigr] = d_\text{in}\,\sigma_A^2\sigma_x^2,
\qquad
\operatorname{Var}\bigl[(BAx)_i\bigr] = r\,\sigma_B^2 \cdot d_\text{in}\,\sigma_A^2\sigma_x^2
$$

The adapter's output variance is **proportional to $r$**, because it is a sum of
$r$ independent contributions. Now apply a scaling $\gamma_r$. For the adapter
branch to contribute at an $r$-independent magnitude we need $\gamma_r^2 \, r$
constant, that is

$$
\gamma_r \propto \frac{1}{\sqrt{r}}
$$

With the conventional $\gamma_r = \alpha/r$ we instead get $\gamma_r^2 r =
\alpha^2/r$, so the adapter's contribution — and the gradient signal reaching
it — is suppressed by an extra factor of $r$ as rank grows. This is the
**gradient collapse** that rank-stabilized LoRA (rsLoRA) identifies: it explains
the widely reported observation that LoRA "stops improving past rank 16 or 32."
Under $\alpha/r$, raising the rank simultaneously adds capacity and turns the
learning rate down, and the two effects cancel.

Practical consequences:

- If you sweep $r$ with $\alpha/r$ scaling, hold $\alpha/r$ fixed by scaling
  $\alpha$ with $r$ (the common "$\alpha = 2r$" folklore), or you are sweeping
  two things at once.
- If you want high rank to actually pay, use $\gamma_r = \alpha/\sqrt{r}$.
- Reported rank ablations that hold $\alpha$ constant while varying $r$ are
  measuring rank confounded with effective learning rate. Read them carefully
  before concluding that "rank does not matter."

## Merge or dynamic adapter?

A LoRA adapter can be merged into the base matrix:

$$
W_\text{merged} = W + \frac{\alpha}{r}BA
$$

After merging, inference uses an ordinary dense matrix. This is fastest for a
single fixed adapter, but it creates one merged copy per variant.

Dynamic adapters keep $W$, $A$, and $B$ separate and apply the low-rank update
at inference time. This preserves flexibility but adds runtime work and
batching complexity.

| Choice | Best when | Cost |
|---|---|---|
| merge | one adapter is fixed for deployment | extra merged copies |
| dynamic | many adapters share one base | adapter routing and overhead |
| hot/cold hybrid | a few popular adapters dominate traffic | operational complexity |

![Side-by-side diagram of one projection computed with a dynamic low-rank branch versus with the adapter folded into the base matrix, annotated with FLOP and memory costs](/courses/model-optimization-systems/lora-merge-vs-dynamic.svg)

One asymmetry deserves emphasis because it catches people. Merging into a
**quantized** base is not the identity operation it is on a BF16 base. You
dequantize $W$, add $(\alpha/r)BA$, and re-quantize — and that final rounding is
applied to a matrix the adapter was never trained against. The adapter learned
to correct a specific quantized $W$; after merging, it is baked into a
*different* quantized matrix. The result is usually close and occasionally is
not, and the only way to know is to evaluate the merged artifact rather than
assuming it inherits the unmerged model's numbers.

## QLoRA memory intuition

If a 70B model is stored in 4-bit form, the raw weight storage is roughly:

$$
70 \times 10^9 \times 0.5 = 35 \text{ GB}
$$

Metadata, optimizer state, activations, gradients for adapters, and framework
overhead add more. Still, this is a different world from BF16 full fine-tuning,
where raw weights alone are about 140 GB and optimizer state can multiply the
requirement.

QLoRA's trick is not only "4-bit weights." It is the combination:

1. keep the base model frozen and quantized;
2. dequantize as needed for computation;
3. train small higher-precision adapters;
4. use optimizer and memory-management techniques that avoid spikes.

### Double quantization: the metadata is not free

"4-bit weights" is never 4 bits. NF4 uses a block size of 64 with one FP32
absmax scale per block, so the true cost per parameter is

$$
4 + \frac{32}{64} = 4.5 \ \text{bits}
$$

That half-bit is 11 percent overhead, and on a 65B model it is 4.1 GB — enough
to decide whether a run fits on a 48 GB card. Double quantization attacks it by
treating the scales as just another tensor to quantize: the FP32 scales are
themselves quantized to FP8 in blocks of 256, with one FP32 scale per block of
scales. The accounting becomes

$$
4 + \underbrace{\frac{8}{64}}_{\text{FP8 scales}}
  + \underbrace{\frac{32}{64 \times 256}}_{\text{scales of the scales}}
= 4 + 0.125 + 0.002 = 4.127 \ \text{bits}
$$

A saving of $0.373$ bits per parameter, or about 3.0 GB on a 65B model. Note
where the second term vanishes: quantizing the scales of the scales would buy
essentially nothing, because $32/(64 \times 256)$ is already 0.002 bits. The
recursion terminates on its own after one level, which is a good sanity check
that the design is not arbitrary.

### Paged optimizers

The remaining failure mode is not average memory but **spikes**. Gradient
checkpointing recomputes activations in bursts, and a long sequence can push a
run that fits comfortably at steady state into OOM for a few milliseconds.
QLoRA allocates optimizer state in NVIDIA unified memory, so those pages
migrate to CPU under pressure and return afterwards. It trades a small amount of
bandwidth during the spike for not crashing, which is the right trade when the
alternative is a smaller batch for the entire run.

## Adapter composition and routing

Once adapters are small, systems start treating them as deployable artifacts.
That creates new patterns:

- per-customer adapters for enterprise behavior;
- task adapters for summarization, coding, retrieval, or classification;
- domain adapters for medicine, law, chemistry, or protein biology;
- routing policies that choose an adapter from the prompt or metadata;
- adapter libraries that can be loaded, evicted, or cached.

Composition is tempting but tricky. Adding two adapters is not guaranteed to
combine their behaviors cleanly. Training order, target modules, rank, and data
distribution all matter. In safety-critical domains, adapter composition needs
the same evaluation discipline as a new model.

## What makes thousands of adapters serveable

The "one base, many deltas" story has an obvious hole. If every request in a
batch wants a different adapter, the low-rank branch is no longer one matmul —
it is $B$ different tiny matmuls with different operands, which is exactly the
shape GPUs are worst at. Naively you would have to group requests by adapter,
which destroys the batching you built the whole serving system around.

The fix is a kernel. Systems in the Punica and S-LoRA line implement a
**batched gather matrix-vector multiply**: a single kernel launch in which row
$i$ of the batch multiplies against adapter $\pi(i)$'s $A$ and $B$, gathered by
index rather than by materializing per-adapter batches. The base GEMM stays one
dense operation for the whole batch; only the rank-$r$ branch gathers. Because
$r$ is tiny, the gather is cheap relative to the base matmul, and heterogeneous
adapters batch together at near-homogeneous throughput.

Two further ideas make the memory side work:

- **Unified paging.** Adapter weights and KV-cache blocks are allocated from the
  same pool in fixed-size pages. An adapter is a resident object with an
  eviction policy, exactly like a cache block, so a serving system can hold
  thousands of adapters with only the hot ones in GPU memory.
- **Heterogeneous ranks in one batch.** Padding every adapter to a common rank
  wastes memory proportional to the largest rank present. Rank-aware kernels
  index each adapter's own $r$, so a rank-8 adapter and a rank-64 adapter can
  share a batch without either being padded to the other.

The lesson generalizes past LoRA: a modeling idea becomes a deployment
architecture only when someone writes the kernel that makes its awkward shape
batchable. Low-rank adaptation was published in 2021; serving thousands of
adapters concurrently became routine once the gather kernels existed.

## Serving cost model

A dynamic LoRA adapter adds two low-rank matmuls around a base projection:

$$
y = Wx + \frac{\alpha}{r}B(Ax)
$$

The base term costs roughly:

$$
2d_\text{out}d_\text{in}
$$

FLOPs for one vector. The LoRA path costs roughly:

$$
2r d_\text{in} + 2d_\text{out}r
$$

FLOPs. With small $r$, that is much cheaper than another dense matrix, but it
is not zero. It can also introduce extra memory reads, layout changes, or
kernel launches if the serving stack does not fuse the adapter path well.

This is why merged adapters remain attractive for hot deployments. If one
adapter receives most traffic, merging removes the dynamic low-rank branch from
the serving path. If thousands of adapters are rarely used, keeping them
separate avoids storing thousands of full merged models. A mature serving
system often uses a hybrid: merge the hottest adapters, keep warm adapters in
GPU memory, and offload cold adapters to CPU or disk.

## Relationship to quantization

Adapters and quantization can be combined in several ways:

| Setup | Base weights | Adapter weights | Use case |
|---|---|---|---|
| LoRA | BF16/FP16 | BF16/FP16 | simple PEFT |
| QLoRA | 4-bit | BF16/FP16 | memory-limited fine-tuning |
| LoftQ-style | quantized | initialized to offset quant error | better low-bit start |
| DoRA-style | either | magnitude and direction split | closer to full-FT update geometry |
| merged adapter | possibly re-quantized | folded into base | fixed deployment |

The two middle rows are worth stating as objectives, since that is where they
differ from plain LoRA.

**LoftQ** notices that QLoRA wastes its adapter's first job. QLoRA quantizes
$W \to Q$, then initializes $BA = 0$, so training starts from a model that is
already wrong by the full quantization error $W - Q$ and must spend capacity
undoing it. LoftQ instead initializes by jointly solving

$$
\min_{Q,\,A,\,B} \ \bigl\lVert W - Q - BA \bigr\rVert_F
$$

alternating two steps that each have a closed form: quantize $W - BA$ to get
$Q$, then take the rank-$r$ truncated SVD of $W - Q$ to get $B$ and $A$. The
adapter starts pointed *at* the quantization error rather than at zero, which
matters most where it hurts most — at 2 and 3 bits, where $\lVert W - Q\rVert$
is large.

**DoRA** starts from a measurement rather than an objective. Decompose each
weight column into magnitude and direction,

$$
W = m \cdot \frac{V}{\lVert V \rVert_c}
$$

and plot how magnitude and direction change during training. Full fine-tuning
and LoRA trace visibly different patterns: LoRA's magnitude and direction
updates are strongly correlated, full fine-tuning's are not. DoRA restores the
freedom by training $m$ directly and applying the low-rank update only to $V$.
The cost is an extra vector per weight matrix, which is negligible; the payoff
is an update geometry that behaves more like the thing it is approximating.

The hard part is preserving quality after all transformations. If you train an
adapter against one quantized base and then merge or re-quantize differently,
you should re-evaluate. The adapter learned in the numerical environment it
saw during training.

## Protein-model deployment

In protein modeling, adapters are especially useful when labeled data is small.
The base model learns broad sequence regularities from millions or billions of
sequences. The adapter learns a narrower mapping from those representations to
an assay or family. Good evaluation should ask:

- Are train and test proteins homologous?
- Does the adapter generalize to unseen families?
- Does it preserve calibration, not just rank order?
- Does it help the downstream wet-lab decision?
- Does quantizing the base change the adapter's conclusions?

Those questions are systems questions as much as ML questions. The deployment
artifact is not "a model"; it is base weights, quantization metadata, adapter
weights, tokenizer or alphabet, preprocessing, and evaluation assumptions.

## Going deeper

- LoRA, the original low-rank adaptation paper: https://arxiv.org/abs/2106.09685
- Intrinsic dimensionality of fine-tuning, the empirical basis for the low-rank bet: https://arxiv.org/abs/2012.13255
- QLoRA, NF4, double quantization, and paged optimizers: https://arxiv.org/abs/2305.14314
- rsLoRA, the variance argument for alpha over root-r scaling: https://arxiv.org/abs/2312.03732
- LoftQ, quantization-aware adapter initialization: https://arxiv.org/abs/2310.08659
- DoRA, weight-decomposed low-rank adaptation: https://arxiv.org/abs/2402.09353
- S-LoRA, serving thousands of concurrent adapters: https://arxiv.org/abs/2311.03285
- Punica, the batched gather kernels that make multi-adapter batching practical: https://arxiv.org/abs/2310.18547
- Hugging Face PEFT documentation: https://huggingface.co/docs/peft
