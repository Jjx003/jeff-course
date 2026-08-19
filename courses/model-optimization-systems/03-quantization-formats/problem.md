# Quantization formats that matter

Quantization is the art of spending fewer bits where precision is less
valuable. That sentence sounds simple, but modern model systems use the word
"quantization" for several different objects:

| Object | Why quantize it? | Common formats |
|---|---|---|
| Weights | Fit larger models and read fewer bytes | INT8, INT4, NF4, FP8, FP4 |
| Activations | Speed matmuls and reduce bandwidth | INT8, FP8, FP4 on newer GPUs |
| KV cache | Fit longer contexts and more users | INT8, FP8, INT4, low-bit cache schemes |
| Optimizer state | Fine-tune with less memory | 8-bit optimizers, paged optimizers |
| Adapter/base split | Train small updates cheaply | QLoRA, LoftQ, low-bit PEFT |

The hard part is not "use fewer bits." The hard part is deciding where to
place quantization levels, which tensors can tolerate error, how much metadata
to store, and whether the serving hardware has kernels that make the lower-bit
format faster rather than merely smaller.

## A first example

Suppose a group of four weights is:

```text
[-1.2, -0.8, -0.1, 0.0]
```

A symmetric INT4 quantizer might choose:

$$
s = \frac{\max |x|}{7} = \frac{1.2}{7}
$$

and then store integers:

$$
q_i = \operatorname{clip}\left(\operatorname{round}(x_i / s), -7, 7\right)
$$

The real-valued reconstruction is:

$$
\hat{x}_i = q_i s
$$

The stored 4-bit values are not meaningful without the scale. That one detail
explains much of practical quantization: low-bit weights are data plus
metadata, and the metadata must be accurate enough and cheap enough.

## Post-training quantization

Post-training quantization (PTQ) compresses a trained model without training it
from scratch. Practical PTQ often uses a small calibration set to estimate
scales, choose group sizes, detect outlier channels, or solve for quantized
weights that preserve layer outputs.

Different methods protect different failure modes:

| Method family | Core idea | What it minimizes |
|---|---|---|
| simple uniform PTQ | choose scales and round | weight error, $\lVert W - \hat{W}\rVert^2$ |
| groupwise quantization | use local scales for small groups | weight error, per group |
| GPTQ-style methods | account for approximate second-order error | **layer output** error, $\lVert WX - \hat{W}X\rVert_F^2$ |
| AWQ-style methods | protect activation-important weight channels | output error, weighted by channel salience |
| SmoothQuant-style methods | move activation outliers into weights | joint weight-and-activation quantizability |

The third column is the one that matters. Notice where the boundary falls:
the first two rows minimize error on the weights, and everything below minimizes
error on what the layer *computes*. Those are different objectives, and a method
that is excellent at the first can be mediocre at the second, because a weight
matters exactly as much as the activations it multiplies.

That single shift — from $\lVert W - \hat{W}\rVert$ to $\lVert WX - \hat{W}X
\rVert$ — is what separates a 2022-era quantizer from a modern one, and it is
also why every method past the second row needs calibration data. You cannot
know which weights matter without seeing what flows through them. The theory
notes derive each objective and show what its closed-form solution looks like.

A useful sanity check when reading a quantization paper: find the objective
function in the first three pages. If the paper does not state one, it is
probably describing a format, not a method, and formats and methods have very
different failure modes.

## NF4 and QLoRA

NF4 is a 4-bit codebook designed for normally distributed weights. Instead of
placing levels evenly like a uniform integer quantizer, it places levels where
normal-distributed values are more likely to occur. QLoRA uses NF4 to keep the
large base model in low-bit storage while training small LoRA adapters in a
higher-precision path.

![Standard normal density with symmetric INT4 levels below it and NF4 levels below that, showing NF4 concentrating levels where the weights actually are](/courses/model-optimization-systems/quant-int4-vs-nf4.svg)

*Both formats spend the same 4 bits and both still need a per-block scale. The
difference is entirely in where the 16 code points are placed. Symmetric INT4
puts five of its levels inside the region holding half the weights and wastes
one code point outright; NF4 puts seven there and uses all sixteen. The theory
notes give the quantile construction and are honest about what "optimal" means
for it.*

That separation changed the economics of fine-tuning. A user can adapt a large
model without storing gradients and optimizer state for every base parameter.
The base model becomes a mostly frozen compressed object; the adapter becomes
the trainable task-specific delta.

## FP8 and FP4

Low-bit floating point is different from integer quantization. FP8 and FP4
encode sign, exponent, and mantissa bits, so they preserve a dynamic range more
naturally than a fixed integer grid. They become attractive when hardware and
serving kernels accelerate them directly.

In 2026, FP8 is mature on high-end NVIDIA and other accelerator paths for many
training and inference workloads. FP4 and NVFP4-style workflows are becoming
important in Blackwell-era inference recipes, but they are more tightly coupled
to hardware support, calibration, and vendor tooling. A format is not
automatically fast because it has fewer bits. It is fast when the full stack
can load it, multiply with it, accumulate safely, and avoid format-conversion
overhead.

## KV-cache quantization

The KV cache is not model weights. It grows with:

$$
\text{batch} \times \text{context length} \times \text{layers}
\times \text{KV heads} \times \text{head dim} \times 2
$$

Long-context serving can run out of KV memory before it runs out of model
weight memory. That is why cache compression, quantized KV cache, and
training-free low-bit cache schemes became a major 2025-2026 research and
product theme.

KV-cache error can also be more dynamic than weight error. The cache stores
values produced by the model on the current request, so ranges can vary by
prompt, layer, head, and time. A good cache quantizer has to be cheap enough to
run online and stable enough not to damage long-context behavior.

## Protein-model angle

Protein language models raise the same questions in a domain where quality
metrics can be less forgiving than chat preference scores. A low-bit protein
model might preserve perplexity on amino-acid sequences while damaging variant
effect prediction, remote homology retrieval, binding-site classification, or
folding confidence. For folding systems, pair features and structure heads may
be more sensitive than the sequence trunk.

That does not mean quantization is unsafe. It means the evaluation target must
match the deployment target. If the model will rank pathogenic variants, test
that. If it will generate embeddings for a downstream classifier, test the
classifier. If it will feed a folding head, test structure metrics, not only
token perplexity.

## Recap

Quantization is not one knob. Weight quantization, activation quantization,
KV-cache quantization, optimizer quantization, and quantized fine-tuning solve
different problems and fail in different ways. The next coding exercise builds a
groupwise INT4 quantizer against a real `torch` weight matrix, packs two codes
into every byte, and measures what group size actually buys once outliers are
present.
