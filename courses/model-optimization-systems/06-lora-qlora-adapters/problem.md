# LoRA, QLoRA, and adapter systems

Full fine-tuning changes every weight in a model. LoRA changes the update rule.
Instead of learning a dense update $\Delta W$ for a weight matrix $W$, LoRA
writes:

$$
W' = W + \frac{\alpha}{r}BA
$$

where:

- $W$ has shape $d_\text{out} \times d_\text{in}$,
- $A$ has shape $r \times d_\text{in}$,
- $B$ has shape $d_\text{out} \times r$,
- $r$ is the adapter rank,
- $\alpha$ is a scaling hyperparameter.

If $r$ is small, the adapter has far fewer trainable parameters than $W$:

$$
\text{params}(\text{LoRA}) = r(d_\text{in}+d_\text{out})
$$

instead of:

$$
\text{params}(W) = d_\text{out}d_\text{in}
$$

For a square $4096 \times 4096$ matrix and rank 16, the dense matrix has over
16 million parameters while the LoRA adapter has about 131 thousand. That is
less than 1 percent for that matrix.

## Why this is a systems trick

LoRA is often introduced as a fine-tuning method, but it is also an
infrastructure primitive:

- one base model can serve many task-specific adapters;
- adapters can be swapped, merged, routed, versioned, or combined;
- QLoRA keeps the base model quantized while training adapters;
- inference can either apply adapters dynamically or merge them into base
  weights;
- adapter storage is small enough to make per-customer or per-task variants
  operationally realistic.

This changes the product shape. Instead of deploying ten full copies of a large
model, a team can deploy one base model plus ten small deltas. That saves
storage and memory, but it introduces new serving questions: which adapter is
active for this request, can requests with different adapters batch together,
and should hot adapters be merged for latency?

## What QLoRA changed

QLoRA combines:

- 4-bit base weights;
- higher-precision adapter weights;
- NF4 quantization for normally distributed weights;
- double quantization of scale metadata;
- paged optimizers to reduce memory spikes.

The base model is mostly frozen and compressed. The trainable state lives in
small adapter matrices. This makes useful fine-tuning possible on much smaller
hardware than full fine-tuning would require.

By 2026, the adapter family is broader. DoRA separates magnitude and direction
updates. LoftQ initializes adapters to compensate for quantization error.
Low-bit PEFT work asks how far below 4 bits the base or adapters can go.
Serving systems increasingly care about multi-adapter batching, adapter
offloading, and routing rather than just training memory.

## Protein-model angle

Adapters are attractive for protein language models because biological tasks
are diverse:

- variant effect prediction;
- family-specific function prediction;
- binding-site prediction;
- mutation scoring;
- solubility or expression prediction;
- structure-aware downstream probes.

A general protein model may already encode useful evolutionary and structural
features. A small adapter can specialize those representations to one assay,
protein family, or laboratory objective. The danger is evaluation leakage:
random splits can put close homologs in both train and test. For biology,
adapter quality should be checked on held-out families, time splits, or
carefully separated assays when possible.

## Recap

LoRA is a low-rank update. QLoRA is a memory plan that trains adapters while
keeping the base model quantized. Adapter systems are a deployment architecture:
one base model, many small deltas, and a choice between merging for speed or
applying dynamically for flexibility.
