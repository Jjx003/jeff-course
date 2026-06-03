# Final review notes

This page is a compact review, not an answer key. It highlights the mental
models that connect the course.

## Roofline reasoning

Every accelerator workload lives somewhere between compute-bound and
memory-bound. Arithmetic intensity is:

$$
\text{arithmetic intensity} =
\frac{\text{FLOPs}}{\text{bytes moved}}
$$

If a workload performs few FLOPs per byte, memory bandwidth dominates. If it
performs many FLOPs per byte and keeps the accelerator fed, compute throughput
dominates.

Low-batch decode often has poor weight reuse compared with training or large
prefill. That is why compression, batching, and serving design can matter so
much for inference.

## Quantization

Quantization reduces bytes per value. Weight-only quantization targets model
parameters. Activation quantization targets intermediate tensors. KV-cache
quantization targets the memory that grows with context length and concurrent
requests.

Important distinctions:

- per-tensor scales are simple but coarse,
- per-channel or groupwise scales preserve more local range information,
- 4-bit methods save more memory but need careful calibration,
- quality must be measured on the downstream task, not just on reconstruction
  error.

## LoRA and QLoRA

LoRA constrains fine-tuning to a low-rank update:

$$
W' = W + BA
$$

where $A \in \mathbb{R}^{r \times d_\text{in}}$ and
$B \in \mathbb{R}^{d_\text{out} \times r}$. The trainable parameter count is
small when $r \ll d_\text{in}, d_\text{out}$.

QLoRA combines low-rank adapters with a quantized frozen base model, reducing
fine-tuning memory pressure while keeping adapter updates trainable.

## Attention and cache

Attention uses:

$$
\text{softmax}\left(\frac{QK^T}{\sqrt{d}}\right)V
$$

The full attention matrix can be large. Tiled exact attention avoids writing
that full matrix by combining block-level softmax statistics.

During decode, KV cache prevents recomputing past keys and values. Cache memory
is a serving resource, not merely a model architecture detail. Long context,
many layers, many heads, and high concurrency all increase pressure.

## Scheduling and speculation

Continuous batching keeps the accelerator busy as requests arrive and finish at
different times. It is a scheduler technique, so the quality contract is request
isolation and fair latency rather than model accuracy.

Speculative decoding is proposal plus verification. The simplified speedup
model is:

$$
\frac{1 + \sum_{i=1}^{k} a^i}{1 + kc_d}
$$

The terms remind you what matters: accepted prefix length and draft overhead.

## Protein and biomolecular workloads

Protein language model workloads often resemble encoder inference over
variable-length sequences. Sequence packing can reduce padding waste when masks
preserve independence.

Structure prediction workloads add geometry. AlphaFold2-style systems use MSAs
and pair representations. AlphaFold3, Chai, and Boltz-style systems broaden the
input and output space to complexes, ligands, nucleic acids, constraints, and
affinity-like signals. Pair and atom-level tensors can change the memory shape
dramatically.

The most important biology rule is humility: a fast confident prediction is not
automatically a correct experimental claim. Validate on the split and metric
that match the scientific question.
