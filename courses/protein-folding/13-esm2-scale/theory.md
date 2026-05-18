## Why does scale help?

The empirical observation: bigger PLMs are better at almost
everything. A diagonal sweep of MLM perplexity, contact-prediction
accuracy, structure-prediction accuracy (for ESMFold), and zero-shot
variant-effect prediction all show monotone improvement from 8M to
15B parameters.

The compressed-database analogy from module 10 gives a clean
explanation: a model with more parameters can store more compressed
patterns. With $4 d^2$ params per attention block (and 4-8 such blocks
plus FFN per layer, multiplied by 30+ layers), the largest models can
in principle memorise extremely fine-grained sequence patterns —
specific motifs, family-specific co-evolutionary signals, even
patterns specific to single Pfam clans.

The practical scaling law (Lin et al, 2023) for ESM-2 was something
like: **MLM loss decreases as a power law in parameter count, with
exponent ~0.07-0.10**. Each doubling of parameters cuts the loss by
~5-7 %. That sounds modest, but it compounds over 11 doublings
(8M → 15B) to halve the loss, and downstream task accuracies improve
disproportionately at the tail.

## VRAM requirements, in detail

For inference (forward pass only):

- **Weights**: $\text{params} \times \text{bytes/param}$. FP32 = 4 B,
  FP16 = 2 B, INT8 = 1 B (with quantisation).
- **Activations**: linear in sequence length, sub-linear in model size
  for the linear layers but $O(L^2)$ for attention.
- **Optimiser states**: only relevant for training. Adam needs ~3x the
  weight memory.

For ESM-2 650M FP16 on a 30-residue sequence:

$$\text{VRAM} \approx \underbrace{650\text{M} \times 2\,\text{B}}_{\text{weights, 1.3 GB}} + \underbrace{30 \times 1280 \times 33 \times 2}_{\text{activations, 2.5 MB}} + \underbrace{\text{matmul scratch}}_{\sim 200 \text{MB}} \approx 1.5\text{ GB}$$

For the same model on a 1024-residue sequence:

$$\text{VRAM} \approx \underbrace{1.3\text{ GB}}_{\text{weights}} + \underbrace{1024 \times 1280 \times 33 \times 2}_{\text{activations, } \sim 85\text{ MB}} + \underbrace{1024^2 \times 20\text{ heads} \times 33\text{ layers} \times 2}_{\text{attention, } \sim 1.4\text{ GB}} + \dots \approx 3.5\text{ GB}$$

The $O(L^2)$ attention term is the long-sequence killer.

## Quantisation for inference

When you can't fit the FP16 model, INT8 quantisation gives ~50 %
memory reduction at the cost of small accuracy degradation:

```python
import torch.ao.quantization as quant
quant_model = quant.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
```

ESM-2 weights quantise reasonably well. For *training* use cases you
don't quantise; for read-only inference at scale, INT8 + FP16 mixed
precision is a solid trade-off.

## Compute vs memory trade-offs

Two practical knobs you'll reach for:

### `model.half()` vs `model.float()`

`.half()` converts to FP16 (2x less memory, slight precision loss).
`.float()` is the default FP32. For ESM-2 inference, `.half()` is
essentially lossless and is the recommended default on any GPU that
supports FP16 (which is almost all modern NVIDIA cards). Cast logits
back to `.float()` before softmax to avoid underflow on the
small-probability tail.

### Attention chunking for long sequences

The native `fair-esm` API exposed `model.set_chunk_size(chunk_size)`,
which processed the $L \times L$ attention matrix in chunks. The
HuggingFace `EsmModel` doesn't expose that directly; for long
sequences the canonical rescues are gradient checkpointing
(`model.gradient_checkpointing_enable()`, but for training only) or
running on `transformers` >= 4.36 with the Flash-Attention backend
(`attn_implementation="flash_attention_2"`), which gets you the same
memory profile via a fused kernel.

## Quality scaling with model size

Empirical observations from the ESM-2 paper:

| Task | 8M | 35M | 150M | 650M | 3B | 15B |
|---|---|---|---|---|---|---|
| Long-range contact prediction (% precision) | 28 | 36 | 47 | 55 | 60 | 64 |
| MLM perplexity (lower = better) | 13.4 | 9.8 | 7.6 | 6.4 | 5.7 | 5.1 |
| ESMFold pTM (avg, CASP14) | 0.42 | 0.55 | 0.66 | 0.74 | 0.79 | 0.82 |

(Numbers approximate; consult the paper for exact ones.)

For the masked-prediction task in this module, the trend is similar:
the 8M model rarely top-1s the correct conserved residue at a high
threshold, while the 650M model regularly gets it with > 70 %
probability. The gap widens for harder positions where the
co-evolutionary signal is more subtle.

## The "compressed database" view at scale

If a 8M model has, in some loose sense, "a few thousand patterns"
compressed into its weights, then a 15B model has "tens of millions
of patterns". The implications:

- **Rare protein families** that the 8M model has effectively never
  seen are well-represented in the 15B model.
- **Subtle co-evolutionary signals** — e.g. "in cytochrome P450 family
  2, the co-conservation between residues 237 and 412 is unusually
  strong" — survive the compression at large scale, are washed out at
  small scale.
- **Generalisation to novel sequences** improves: a 15B model has seen
  enough variation to interpolate between known families.

This last point is the empirical bedrock of ESM3's "design a novel
fluorescent protein" demo (module 14): scale + multimodal training
together push the model into a regime where it can produce sequences
that are neither memorised nor extrapolations along a single axis,
but truly novel combinations of known patterns.

## When smaller wins

Bigger isn't always the right call:

- **Throughput-bound workloads.** Filtering a billion sequences with
  the 15B model would take longer than the heat death of the
  universe; the 8M is happy on CPU.
- **Latency-bound workloads.** Real-time per-request inference
  (e.g. an active-learning loop or a UI feedback loop) wants the
  fastest model that still works.
- **Fine-tuning.** Training the 15B model from scratch is impossible
  for individuals; even fine-tuning needs serious infrastructure. The
  650M is the largest model most people fine-tune.

For *zero-shot* property predictions on a small number of sequences,
go big. For *high-throughput screening*, go small.

## How the 15B fits on what hardware

Concrete data points:

- **NVIDIA A100 (80 GB)**: fits 15B in FP16 with room to spare.
- **NVIDIA RTX 4090 (24 GB)**: fits 3B in FP16; not 15B.
- **NVIDIA RTX 3090 (24 GB)**: same.
- **NVIDIA A6000 (48 GB)**: fits 15B in INT8 quantisation, or 3B
  comfortably in FP16.
- **CPU-only laptop**: can technically load 8M and run inference,
  slowly. Anything bigger needs swap and is impractically slow.

If you have access to multiple GPUs, ESM-2's checkpoints can be
sharded across devices; `accelerate` and `DeepSpeed` are the standard
tools. The exercise here doesn't go there because most learners are
running single-GPU.
