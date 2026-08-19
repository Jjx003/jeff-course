# Final test: optimization systems

This is the cumulative assessment for the model optimization systems course. It
covers the whole arc:

- roofline reasoning and memory bandwidth,
- weight and activation precision,
- quantization tradeoffs,
- LoRA and QLoRA,
- fused and tiled attention,
- KV-cache serving,
- continuous batching,
- speculative decoding,
- protein language model workloads,
- biomolecular structure-prediction systems.

Unlike a quiz, this test records your answers during the attempt and reveals
correctness only after you finish. Treat it like a short engineering exam: slow
down, do the units, and make each answer justify itself.

## How to approach the test

A good optimization engineer does not memorize tricks as isolated names. They
ask:

1. What operation dominates the workload?
2. Is the bottleneck compute, memory bandwidth, memory capacity, scheduling, or
   data preprocessing?
3. What approximation or compression is being introduced?
4. What correctness or quality signal must remain valid?
5. Which metric would prove the optimization helped?

Use that checklist for every question. If two answer choices sound plausible,
the resource being saved usually separates them.

## Course-level themes

### Small arithmetic beats vague intuition

Raw model storage follows:

$$
\text{bytes} = \text{parameters} \times \frac{\text{bits per parameter}}{8}
$$

LoRA trainable parameters for a single adapted matrix follow:

$$
r(d_\text{in} + d_\text{out})
$$

KV-cache size grows with layers, heads, context length, head dimension, and
bytes per value. Pair representations in protein structure models often grow
quadratically with sequence length.

If you keep the units straight, many questions become simple.

### Exactness and approximation are different

Some optimizations change how an exact computation is scheduled. FlashAttention
is the central example: it computes exact attention while reducing memory
traffic. Other optimizations compress or approximate something: quantization
changes numeric representation, adapters restrict the trainable update,
speculative decoding uses a proposal mechanism with target verification.

The test may ask you to distinguish these categories. Do not assume every speed
trick is an approximation.

### LLM systems and protein systems rhyme

LLM serving and protein modeling share several systems instincts:

- avoid wasted memory traffic,
- reuse cached computation,
- batch similar shapes together,
- use cheap stages before expensive stages,
- validate against the metric that matters.

They diverge in their correctness contracts. Text generation is about target
model distributions, latency, and user-facing token streams. Biomolecular
prediction is about geometry, confidence, assay relevance, and biological
generalization.

## When you finish

Use the results screen as a map for review. A miss on a formula suggests unit
practice. A miss on serving suggests phase classification. A miss on biology
usually means the workload shape or validation target was blurred.
