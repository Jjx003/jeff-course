## Goal

Compare five practical ESM-2 sizes — **8M, 35M, 150M, 650M, 3B** —
on the masked-prediction task from module 11, then attempt the **15B**
model (likely to OOM on consumer hardware) with a try/except. Print:

1. A reference table of all six ESM-2 sizes with their parameter
   counts and estimated VRAM footprints.
2. The actual loaded parameter counts for each checkpoint that fits.
3. The forward-pass time (best of 3 runs) on the same input sequence.
4. The top-1 predicted residue and its probability for a single
   masked position — at each size.

You should see two trends:

- **Quality improves monotonically with scale.** The 8M model gives a
  flat, noisy distribution; the 650M model is sharply concentrated on
  the biologically correct answer; 3B sharper still.
- **Time grows roughly with parameters.** The bigger models are
  slower — but for a 30-residue sequence the absolute time is still
  small on any modern GPU.

## ESM-2 size table

These are the six canonical sizes in the ESM-2 family. The HuggingFace
identifier prefix `facebook/esm2_t<N>_<size>_UR50D` encodes:

- `t<N>` — number of **transformer layers** (6, 12, 30, 33, 36, 48).
  Note: it is **not** the hidden dim. The hidden dim grows with
  parameter count but is a separate axis (320 → 5120).
- `<size>` — rough parameter count (8M → 15B).
- `UR50D` — pretraining set: UniRef50, deduplicated.

| HuggingFace id | Layers | Params | Embed dim | VRAM (FP16, weights only) |
|---|---|---|---|---|
| `facebook/esm2_t6_8M_UR50D` | 6 | 8 M | 320 | ~16 MB |
| `facebook/esm2_t12_35M_UR50D` | 12 | 35 M | 480 | ~70 MB |
| `facebook/esm2_t30_150M_UR50D` | 30 | 150 M | 640 | ~300 MB |
| `facebook/esm2_t33_650M_UR50D` | 33 | 650 M | 1280 | ~1.3 GB |
| `facebook/esm2_t36_3B_UR50D` | 36 | 3 B | 2560 | ~6 GB |
| `facebook/esm2_t48_15B_UR50D` | 48 | 15 B | 5120 | ~30 GB |

Add activations + matmul scratch on top of "weights only" — typical
GPU footprint at inference is roughly 1.5-2× the weights column.

The 15B model is **out of reach for typical desktop GPUs**. A simple
"weights in FP16" calculation:

$$15 \times 10^9\ \text{params} \times 2\ \text{bytes/param} = 30\ \text{GB}$$

That's just the weights — activations during the forward pass need
another few GB on top. An 80 GB A100 / H100 can run it; almost nothing
else can. The 3B model in FP16 fits comfortably in 16 GB and is the
useful upper bound for most consumer cards (24 GB RTX 4090, 24 GB
RTX 3090, 16 GB workstation cards with some pruning).

## The exercise

1. Print the size table from problem.md.
2. For each of `8M`, `35M`, `150M`, `650M`, `3B`:
   - Load the corresponding `facebook/esm2_*` checkpoint via
     `EsmForMaskedLM.from_pretrained(...)`.
   - Time three forward passes through the same masked input
     sequence. Use the best (minimum) time — first runs include CUDA
     warm-up overhead.
   - Extract the top-1 predicted amino acid and its probability for
     the masked position.
   - Wrap the load + forward in `try/except` so an OOM on one size
     doesn't abort the whole sweep.
3. Print a comparison table at the end for everything that fit.
4. Attempt to load the 15B model with a try/except and a single
   1-token forward pass, reporting the failure mode (OOM, missing
   weights, etc).

## Sequence

Same as module 11:

```text
MGLSDGEWQLVLNVWGKVEADIPGHGQEVL
```

with `<mask>` inserted at position 14 (the conserved `W`).

## Expected output (illustrative)

```text
ESM-2 model size reference
  Name                               Params   Embed dim   VRAM (FP16, weights only)
  facebook/esm2_t6_8M_UR50D             8 M   320         ~16 MB
  facebook/esm2_t12_35M_UR50D          35 M   480         ~70 MB
  facebook/esm2_t30_150M_UR50D        150 M   640         ~300 MB
  facebook/esm2_t33_650M_UR50D        650 M   1280        ~1.3 GB
  facebook/esm2_t36_3B_UR50D            3 B   2560        ~6 GB
  facebook/esm2_t48_15B_UR50D          15 B   5120        ~30 GB

Loading facebook/esm2_t6_8M_UR50D ...
  Parameters: 7,840,737
  Forward time (best of 3): 0.0123 s
  Masked position 14 top-1: K  p=0.1547

Loading facebook/esm2_t12_35M_UR50D ...
  Parameters: 33,665,889
  Forward time (best of 3): 0.0184 s
  Masked position 14 top-1: L  p=0.2731

Loading facebook/esm2_t30_150M_UR50D ...
  Parameters: 148,796,673
  Forward time (best of 3): 0.0312 s
  Masked position 14 top-1: W  p=0.5104

Loading facebook/esm2_t33_650M_UR50D ...
  Parameters: 651,765,424
  Forward time (best of 3): 0.0521 s
  Masked position 14 top-1: W  p=0.7421

Loading facebook/esm2_t36_3B_UR50D ...
  Parameters: 2,841,920,257
  Forward time (best of 3): 0.1184 s
  Masked position 14 top-1: W  p=0.8612

Comparison
  Size     Top-1   p(top-1)   Forward (s)
  8M       K       0.1547     0.0123
  35M      L       0.2731     0.0184
  150M     W       0.5104     0.0312
  650M     W       0.7421     0.0521
  3B       W       0.8612     0.1184

Attempting to load facebook/esm2_t48_15B_UR50D (likely to fail) ...
  15B load failed: OutOfMemoryError
  This is expected on most desktop GPUs (15B needs ~30 GB VRAM).
```

(Numbers vary; this is what a successful run looks like, not what the
grader checks.)

### Where this story goes next

The "scale wins monotonically" picture above was the consensus in
2022-2023. By late 2025 the field had measured a different pattern on
downstream transfer tasks: sequence-only PLM performance on fitness
benchmarks plateaus around 1 B parameters and *declines* past ~5 B.
EvolutionaryScale's **ESM Cambrian (ESMC)** release in December 2024
made the headline crisp: **ESMC 300 M matches ESM-2 650 M** at roughly
half the parameter count. The monotonic improvement you see in this
exercise is real for masked-token prediction; for transfer it tops out
sooner than the 8 M → 3 B curve suggests. Module 23 unpacks the
scaling-wall story and the modern alternatives.

## What you should learn

- **Scale matters, monotonically.** Inference quality on biologically
  meaningful tasks is a smooth function of parameter count, all the
  way up to 15B. There's no "diminishing returns at 650M" point —
  bigger keeps being better, just at higher VRAM cost.
- **VRAM dominates the practical model choice.** Most users never run
  15B. 650M is the sweet spot for desktop GPUs; 3B for serious
  workstations; 15B for institutional clusters.
- **Forward-pass time scales sub-linearly with parameters** for short
  sequences, because compute is bottlenecked by the matmul kernels'
  setup cost, not by parameter count. For long sequences (where
  $O(L^2)$ attention dominates), the scaling is closer to linear.
- **Smaller models are useful too.** For triage / filtering tasks
  where you process millions of sequences, the 8M model is fast
  enough to run on CPU at meaningful throughput.
