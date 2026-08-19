# The optimization stack after intro ML

Most college ML courses teach a clean story: define a loss, choose an optimizer,
train a model, report a benchmark. Production model work starts after that
story ends. The practical question is:

> How do we make a useful model fit, run fast, stay accurate enough, and serve
> many requests without wasting expensive silicon?

This course is about that systems layer. We will use large language models as
the main thread because they make the bottlenecks visible: a single generated
token can require reading billions of parameters, touching a growing KV cache,
and launching many kernels whose individual math looks simple but whose memory
traffic dominates wall-clock time. We will also repeatedly map the same ideas
onto protein language models and folding systems, where sequence length,
pairwise features, templates, diffusion sampling, and all-atom heads create
their own pressure points.

By 2026, "optimize the model" rarely means one trick. It means reasoning across
a stack:

| Layer | Main question | Examples |
|---|---|---|
| Numerics | What precision is enough? | BF16, FP8, FP4, INT8, INT4, NF4 |
| Weight compression | Can we fit and read less? | PTQ, AWQ, GPTQ, groupwise INT4 |
| Adaptation | Can we specialize cheaply? | LoRA, QLoRA, DoRA, adapter routing |
| Kernels | Can the math run as one efficient program? | FlashAttention, fused MLPs, Triton kernels |
| Serving memory | Can we keep active requests resident? | KV cache layout, paging, prefix reuse |
| Decoding | Can we generate fewer expensive steps? | speculative decoding, draft heads, batching |
| Parallelism | Can the model span GPUs without drowning in communication? | tensor/pipeline/expert parallel, collectives |
| Workload shaping | Can we feed the accelerator better inputs? | sequence packing, bucketing, routing |
| Measurement | Did it actually get faster, for whom? | TTFT/ITL percentiles, load curves, honest load generation |

This first module is a map. The rest of the course fills in the parts with
small exercises: a roofline estimator, an INT4 quantizer, a LoRA merge, a
streaming softmax, a continuous batching simulator, a speculative decoding
simulator, a tensor-parallel transformer block, a serving-latency benchmark,
and a protein sequence-packing heuristic.

## Why inference feels different from training

Training looks compute-hungry because every token participates in forward and
backward passes, activations must be saved or recomputed, and optimizer state
can be several times larger than the weights. Inference has a different shape.
Autoregressive inference has two phases:

1. **Prefill:** process the prompt in parallel and build the KV cache.
2. **Decode:** generate one new token at a time, reusing cached keys and values.

Prefill often has large matrix multiplications and enough parallel work to keep
Tensor Cores busy. Decode at small batch sizes can be much less glamorous: the
server may read most of the model weights for each token, perform a relatively
small amount of work per byte loaded, then append another slice to the KV cache.

That is why a 70B model can be memory-bandwidth bound even on a GPU with huge
advertised FLOP/s. Peak compute is not the same as useful token throughput.
The machine may be able to perform nearly a petaflop of BF16 work per second,
but if every generated token requires re-reading about 140 GB of BF16 weights,
memory bandwidth sets a hard lower bound.

## The four budgets to keep in your head

For transformer inference, keep four budgets in view:

| Budget | What it measures | Typical pressure |
|---|---|---|
| Weight memory | Parameters read per generated token | Decode, especially low batch |
| Activation memory | Temporary tensors inside layers | Prefill, training, long prompts |
| KV cache | Stored keys and values from previous tokens | Long context, many active users |
| Kernel overhead | Launches, layout changes, unfused operations | Small batches, fragmented graphs |

The first coding module will quantify the two simplest lower bounds:

$$
t_\text{memory} \ge \frac{\text{bytes moved}}{\text{memory bandwidth}}
$$

$$
t_\text{compute} \ge \frac{\text{FLOPs}}{\text{peak FLOPs}}
$$

These are not predictions; they are floors. Real systems lose time to
synchronization, non-ideal layouts, cache misses, scheduler decisions, network
communication, CPU overhead, and kernels that do not hit the advertised peak.
Still, the larger floor is a good first guess at the bottleneck.

## Arithmetic intensity, derived rather than asserted

The two floors above compete, and the ratio between them has a name. Define
**arithmetic intensity** as work per byte moved:

$$
I = \frac{F}{B}
$$

A kernel is memory-bound when $t_\text{memory} > t_\text{compute}$, which after
substituting the two floors is exactly the condition

$$
\frac{B}{\beta} > \frac{F}{\phi}
\quad\Longleftrightarrow\quad
I < \frac{\phi}{\beta}
$$

The quantity $\phi/\beta$ depends only on the hardware. It is called the
**ridge point**, and it is the single most useful number to memorize about an
accelerator. For an H100 SXM at 989 BF16 TFLOP/s and 3.35 TB/s of HBM3:

$$
I^{*} = \frac{989 \times 10^{12}}{3.35 \times 10^{12}} \approx 295
\ \text{FLOP/byte}
$$

Below 295 FLOPs per byte, the memory system sets the pace no matter how good
your kernels are. Above it, you are finally paying for the Tensor Cores.

Now compute $I$ for a decode step. A decoder-only model with $N$ parameters
costs about $2N$ FLOPs per token — one multiply and one add per weight. If
weights are stored at $b$ bytes each and the batch contains $B$ sequences all
generating a token at the same time, then the weights are read **once** for the
whole batch:

$$
F = 2NB, \qquad \text{bytes} = bN, \qquad
I = \frac{2NB}{bN} = \frac{2B}{b}
$$

The parameter count cancels. Intensity during decode does not depend on how big
the model is — only on the batch size and the weight format:

| Weight format | $b$ | $I$ | Batch needed to reach $I^{*} = 295$ |
|---|---:|---:|---:|
| BF16 | 2 | $B$ | 295 |
| FP8 | 1 | $2B$ | 148 |
| INT4 | 0.5 | $4B$ | 74 |

This one table explains a great deal of production practice. At batch 1 in
BF16, intensity is 1 and the GPU delivers about $3.35$ TFLOP/s — roughly
0.3 percent of its rated peak. Nothing is broken; the machine is simply waiting
on memory. Batching and quantization are the two levers that move you right
along the axis, and the table says how far each one moves you.

![Roofline for one H100 SXM with batch-1 decode, batch-32 decode, INT4 decode, and long-prompt prefill marked as operating points](/courses/model-optimization-systems/stack-roofline.svg)

*The same hardware, four workloads. Prefill sits past the ridge point because a
2048-token prompt reuses each weight 2048 times. Decode has to buy its reuse
with batch size, and the KV cache is what makes batch size expensive.*

Notice what the table does **not** say. It does not say INT4 makes decode four
times faster; it says INT4 moves you four times further right, and the speedup
you collect depends on where you started. Going from $I=1$ to $I=4$ on the
sloped roof is a genuine 4× because you are bandwidth-limited the whole way.
Going from $I=200$ to $I=800$ buys you almost nothing, because you were already
past the ridge and the flat roof caps you. Quantization is a bandwidth
optimization that happens to also save storage, and it stops paying at exactly
the point where the workload stops being bandwidth-bound.

## Why protein models belong in this course

Protein models are not just LLMs with a different alphabet. They inherit many
transformer bottlenecks, then add biological structure:

- protein sequence lengths are highly variable, so padding waste matters;
- pair representations scale like $O(L^2)$, not $O(L)$;
- MSA search and template retrieval can dominate wall-clock time;
- structure modules carry geometry-specific tensors;
- recycling, diffusion, or sampling repeats computation;
- complex prediction adds chains, ligands, nucleic acids, and constraints.

An optimization that helps chat serving may only partly help structure
prediction. FlashAttention can reduce attention memory, but it does not remove
the cost of an all-atom head. Weight quantization can reduce model footprint,
but it does not solve template database latency. Sequence packing can raise GPU
utilization, but careless packing can mix examples in ways the model was not
trained to expect. The right question is always: which bottleneck is active for
this workload?

## A running example: the same model in three places

Imagine a 70B decoder-only model used in three modes:

| Mode | Workload | Likely first bottleneck |
|---|---|---|
| Offline summarization | long prompts, large batches | compute and activation memory |
| Interactive chat | small batches, token streaming | weight bandwidth and scheduler overhead |
| Long-context retrieval | many 64k-token sessions | KV cache capacity and cache bandwidth |

The weights are the same. The hardware may be the same. The bottleneck changes
because the request shape changes. This is the main habit the course tries to
build: do not attach an optimization to a model in the abstract. Attach it to a
workload, a hardware target, and a quality constraint.

## Course promise

You will not write a production inference server from scratch. You will write
small, inspectable pieces that make a production server less mysterious:

- a roofline-style token budget,
- a groupwise INT4 quantizer,
- a low-rank adapter parameter calculation,
- streaming attention arithmetic,
- a continuous batching simulation,
- a speculative decoding simulation,
- a tensor-parallel transformer block verified against its unsharded twin,
- a latency benchmark calibrated against a queueing-theory closed form,
- and a sequence-packing heuristic for protein workloads.

The goal is taste. Taste means knowing that INT4 weight-only quantization helps
one problem, KV-cache quantization helps another, and neither automatically
fixes a bad batching policy. It means asking whether an FP8 benchmark used
native hardware support, whether a LoRA adapter was merged or applied
dynamically, and whether a protein benchmark used random splits that leak
family-level similarity.

## Recap

Modern model optimization is an end-to-end systems problem. The same model can
be memory-bound, compute-bound, cache-bound, or scheduler-bound depending on
request shape. The next module starts with the simplest useful tool: a
roofline-style budget for one generated token. You will then measure your own
machine with `torch` and see how far real throughput sits from the vendor's peak
numbers — which is the first lesson in why the roofline gives lower bounds on
latency rather than predictions of it.
