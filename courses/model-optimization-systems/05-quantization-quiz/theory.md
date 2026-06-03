# Review: three compression stories

Quantization appears in this course in three different stories.

## 1. Weight storage and bandwidth

Weights are fixed after training or loading. Compressing them can:

- make a larger model fit on a device;
- reduce bytes read during decode;
- reduce storage and deployment size.

For a model with $P$ parameters and $b$ bytes per parameter:

$$
\text{weight bytes} = P b
$$

That is the term you estimated in the roofline module. Weight-only INT4 mainly
attacks this storage/bandwidth term. It may or may not accelerate compute,
depending on kernels and hardware.

## 2. Activation and low-bit matmul throughput

Activations depend on the input. Quantizing them can enable faster low-bit
matmuls, but it is more sensitive because ranges change by prompt, layer, and
batch. FP8 is a mature example on supported accelerators; FP4-style workflows
are increasingly important in newer inference stacks but remain tightly tied to
vendor kernels and calibration recipes.

The key question is whether the whole path is optimized:

$$
\text{load} \rightarrow \text{dequantize or multiply} \rightarrow
\text{accumulate} \rightarrow \text{store}
$$

If format conversion dominates, fewer bits may not mean lower latency.

## 3. KV cache capacity

The KV cache grows with context length and active requests:

$$
\text{KV bytes} =
L \times T \times H_\text{kv} \times D \times 2 \times b
$$

where $L$ is layers, $T$ is tokens, $H_\text{kv}$ is KV heads, $D$ is head
dimension, and $b$ is bytes per value.

Weight quantization does not automatically reduce this term. GQA, cache
quantization, cache paging, prefix reuse, and eviction policies are separate
serving decisions.

## QLoRA as a bridge

QLoRA is a fine-tuning memory plan, not just a quantization format. It keeps
the base model compressed and frozen while training small adapter matrices in a
higher-precision path. The memory savings come from avoiding full gradients and
optimizer state for every base parameter.

This is why QLoRA belongs between quantization and adapters. It uses low-bit
base weights, but the thing being learned is a low-rank update.

## Protein-model check

For protein models, ask which biological output must survive compression:

| Model use | Failure mode to test |
|---|---|
| sequence embeddings | downstream probe degradation |
| variant scoring | rank correlation on held-out assays |
| remote homology | retrieval drop on distant families |
| folding | structure metric or confidence drift |
| complex prediction | interface and ligand-placement errors |

Do not assume a quantization method that works for chat preserves a protein
model's geometry-sensitive behavior.
