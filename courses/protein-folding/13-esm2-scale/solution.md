## Walkthrough

### Loading by id

```python
tokenizer = AutoTokenizer.from_pretrained(hf_name)
model = EsmForMaskedLM.from_pretrained(hf_name)
```

Every `facebook/esm2_t*_UR50D` checkpoint is a sibling on the
HuggingFace Hub, so the same two-liner loads any of the six sizes
just by changing the `hf_name` string. We use `EsmForMaskedLM` (not
`EsmModel`) because we want the MLM logits, not just hidden states.

### Why `model.half()` on GPU?

```python
if device == "cuda":
    model = model.half().to(device)
```

FP16 cuts memory in half compared to FP32, with negligible accuracy
loss for ESM-2's MLM logits. On a 24 GB GPU you could fit the 3B
model in FP32; on most consumer GPUs, FP16 is required for the 650M.

For the 15B model, even FP16 is not enough on consumer hardware —
the weights alone are 30 GB.

### Timing with `torch.cuda.synchronize`

```python
torch.cuda.synchronize()
t0 = time.perf_counter()
with torch.inference_mode():
    model(**inputs)
torch.cuda.synchronize()
times.append(time.perf_counter() - t0)
```

GPU operations launch asynchronously by default. Without explicit
synchronisation, the `time.perf_counter()` would measure how long it
took to *queue* the operation, not how long it took to *complete*.

The `n_warmup` calls are critical too: the first GPU call after
loading a model includes JIT compilation, kernel selection, and
allocation overhead that you don't want polluting the timing.

### Logits in FP16

When the model is in FP16, the logits come back in FP16 too. We cast
to FP32 before softmax to avoid potential overflow / underflow:

```python
aa_probs = torch.softmax(logits[aa_ids].float(), dim=-1)
```

For ESM-2's logit values this rarely matters in practice, but it's
the correct habit.

### Cleaning up between models

```python
del model
torch.cuda.empty_cache()
```

PyTorch is conservative about freeing GPU memory; the explicit
`del + empty_cache()` pair guarantees the smaller model is gone
before we load the bigger one. Without these, you can OOM partway
through the sweep.

## Reading the comparison

The expected pattern (numbers vary per run):

| Model | Top-1 letter | p(top-1) |
|---|---|---|
| 8M | not always `W`; often `K` or `L` | ~0.10-0.20 |
| 35M | mixed `W` / `L` / `F` | ~0.20-0.35 |
| 150M | usually `W` | ~0.45-0.60 |
| 650M | `W` | ~0.70-0.85 |
| 3B | `W` (sharper still) | ~0.85-0.92 |

The 8M model has fewer than 1/80th the parameters of the 650M. Its
attention weights and FFN matrices simply can't compress enough of
the globin family's statistics to nail down the conserved `W`. The
650M model can; the 3B sharpens the distribution further.

The same scale-quality story plays out across more sophisticated
benchmarks too — long-range contact prediction, ESMFold accuracy,
zero-shot variant-effect prediction. ESM-2's paper (Lin et al, 2023)
documents this in detail.

## Why time scales sub-linearly with parameters (for short sequences)

The 8M model has 80x fewer parameters than the 650M, but only 4-5x
faster forward time on a 30-residue input. The gap is much wider on
hardware with high matmul throughput because:

- **Kernel launch overhead is fixed** per layer regardless of size.
- **Attention's $L^2$ term is small** for $L = 30$, so the model
  size dominates only weakly.
- **GPU compute units saturate** more efficiently on larger matmuls,
  so each FLOP is cheaper at 1280-d than at 320-d.

For long sequences, the relationship flips toward linear-in-params
because the matmuls genuinely dominate kernel-launch overhead.

## The 15B story

Three plausible failure modes when loading the 15B:

1. **`OutOfMemoryError`** on GPU. Most common on cards with < 32 GB.
2. **`RuntimeError: Expected ... bytes available`** — happens when
   PyTorch tries to allocate the FP32 weights and finds insufficient
   RAM (~60 GB at FP32).
3. **Cache miss / network timeout** — HuggingFace's `from_pretrained`
   will try to download ~30 GB of weights into `~/.cache/huggingface/`
   on first use. On a slow connection this can hang or partially
   download.

The exercise's `try/except` is a graceful way to demonstrate the
failure without crashing. We attempt only a **single 1-token forward
pass** (`tokenizer("M", return_tensors="pt")`) inside the try block,
so that on the rare hardware where 15B does fit we exercise the API
without committing to a full timed sweep. In production, you'd guard
model loading with explicit VRAM checks via
`torch.cuda.mem_get_info()`.

## Connection to the rest of the course

The scaling story underlies several later modules:

- **Module 17** (ESMFold vs MSA): ESMFold needs the 15B model to
  match AlphaFold2 quality. Smaller PLMs underperform.
- **Module 22** (Lead optimisation): the choice of which size to
  evotune from is a real trade-off — bigger gives better embeddings
  but more compute cost per forward pass during the optimisation
  loop.

For most of this course we use the 650M as the default — it's the
sweet spot for desktop GPU inference and gives "good enough" answers
on the demos.
