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
| Workload shaping | Can we feed the accelerator better inputs? | sequence packing, bucketing, routing |

This first module is a map. The rest of the course fills in the parts with
small exercises: a roofline estimator, an INT4 quantizer, a LoRA merge, a
streaming softmax, a continuous batching simulator, a speculative decoding
simulator, and a protein sequence-packing heuristic.

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
roofline-style budget for one generated token.
