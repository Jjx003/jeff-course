## Hints

1. The size table holds the HuggingFace id plus display fields:

```python
SIZE_TABLE = [
    ("facebook/esm2_t6_8M_UR50D",    "8M",   "8 M",   "320",  "~16 MB"),
    ("facebook/esm2_t12_35M_UR50D",  "35M",  "35 M",  "480",  "~70 MB"),
    ("facebook/esm2_t30_150M_UR50D", "150M", "150 M", "640",  "~300 MB"),
    ("facebook/esm2_t33_650M_UR50D", "650M", "650 M", "1280", "~1.3 GB"),
    ("facebook/esm2_t36_3B_UR50D",   "3B",   "3 B",   "2560", "~6 GB"),
    ("facebook/esm2_t48_15B_UR50D",  "15B",  "15 B",  "5120", "~30 GB"),
]
```

2. Loading any checkpoint by id (HuggingFace `transformers`):

```python
from transformers import AutoTokenizer, EsmForMaskedLM

tokenizer = AutoTokenizer.from_pretrained(hf_name)   # e.g. "facebook/esm2_t6_8M_UR50D"
model = EsmForMaskedLM.from_pretrained(hf_name)
```

The first run downloads each checkpoint to `~/.cache/huggingface/`;
subsequent runs are cached and load in seconds.

3. Timing a forward pass:

```python
import time

def time_forward(model, inputs, n_warmup=1, n_runs=3):
    use_cuda = inputs.input_ids.is_cuda
    for _ in range(n_warmup):
        with torch.inference_mode():
            model(**inputs)
        if use_cuda:
            torch.cuda.synchronize()
    times = []
    for _ in range(n_runs):
        if use_cuda:
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.inference_mode():
            model(**inputs)
        if use_cuda:
            torch.cuda.synchronize()
        times.append(time.perf_counter() - t0)
    return min(times)
```

The `torch.cuda.synchronize()` calls are critical — without them
GPU calls are launched asynchronously and your timing is meaningless.

4. Top-1 prediction lookup:

```python
def top1_at(model, tokenizer, masked_seq, device):
    inputs = tokenizer(masked_seq, return_tensors="pt").to(device)
    mask_index = int(
        (inputs.input_ids[0] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0].item()
    )
    with torch.inference_mode():
        out = model(**inputs)
    logits = out.logits[0, mask_index]
    aa_letters = "ACDEFGHIKLMNPQRSTVWY"
    aa_ids = torch.tensor(
        [tokenizer.convert_tokens_to_ids(c) for c in aa_letters], device=device
    )
    aa_probs = torch.softmax(logits[aa_ids].float(), dim=-1)
    top1 = int(aa_probs.argmax().item())
    return aa_letters[top1], float(aa_probs[top1].item())
```

We locate the mask programmatically (`(input_ids == mask_token_id).nonzero(...)`)
rather than hard-coding the token index — robust to any string the
tokenizer might prepend.

5. The 15B attempt should be wrapped in try/except:

```python
try:
    tok = AutoTokenizer.from_pretrained("facebook/esm2_t48_15B_UR50D")
    m = EsmForMaskedLM.from_pretrained("facebook/esm2_t48_15B_UR50D")
    if device == "cuda":
        m = m.half().to(device)
    # Single 1-token forward pass — just verifies the API works on the
    # rare hardware that can fit the weights.
    with torch.inference_mode():
        m(**tok("M", return_tensors="pt").to(device))
    print("15B loaded successfully (you have impressive hardware!)")
except Exception as e:
    print(f"15B load failed: {type(e).__name__}: {e}")
    print("This is expected on most desktop hardware — the 15B model")
    print("requires ~30 GB VRAM in FP16, beyond what consumer GPUs offer.")
```

HuggingFace's `from_pretrained` will either succeed (and then likely
OOM on `.to(device)`) or fail during the streaming weight load if the
host RAM is too small. Either failure mode is caught here.

## Memory tips

- **Free the small model before loading the big one.** Python's GC is
  lazy about CUDA tensors; `del model_8m; torch.cuda.empty_cache()` is
  the explicit form.
- **Use FP16 for everything > 150M.** `model = model.half().to(device)`.
- **Batch size 1.** The exercise uses a single sequence; don't try to
  batch — the marginal speedup isn't worth the memory hit.

## Sanity checks

- The actual `Parameters: ` printed line should match the size table
  ($\pm$ rounding) — `7,840,737` for 8M, `651,765,424` for 650M.
- The 8M model's top-1 probability for the masked `W` is rarely
  > 30 %; the 650M's is typically > 70 %. If your numbers are close,
  something is wrong (most likely you're using the same model twice).
- Forward-pass times on GPU: 8M is sub-20 ms, 650M is sub-100 ms for
  a 30-residue input. CPU timings are roughly 50-200x larger.

## Going deeper

- **Lin et al, 2023** — *Evolutionary-scale prediction of atomic-level protein structure* — [https://www.science.org/doi/10.1126/science.ade2574](https://www.science.org/doi/10.1126/science.ade2574). The ESM-2 paper. Section 2 describes the scaling sweep and downstream evaluation.
- **Hoffmann et al, 2022** — *Training Compute-Optimal Large Language Models* — [https://arxiv.org/abs/2203.15556](https://arxiv.org/abs/2203.15556). The "Chinchilla" paper on language model scaling laws. Most of the intuition translates to PLMs.
- **HuggingFace ESM model page** — [https://huggingface.co/facebook/esm2_t33_650M_UR50D](https://huggingface.co/facebook/esm2_t33_650M_UR50D). All six `facebook/esm2_*` checkpoints are siblings on the Hub; the model card lists weights, training details, and citation.
- **`bitsandbytes`** — [https://github.com/TimDettmers/bitsandbytes](https://github.com/TimDettmers/bitsandbytes). The standard quantisation library for fitting big transformers on small GPUs.
- **`accelerate`** — [https://huggingface.co/docs/accelerate](https://huggingface.co/docs/accelerate). HuggingFace's library for sharding models across multiple GPUs / CPU offload. The way to run 15B on consumer hardware.

## Things to try after

1. Plot "forward time vs param count" across the five sizes you ran.
   On short inputs the curve is sub-linear; on long inputs (e.g. 500
   residues) it bends toward linear as the $O(L^2)$ attention term
   starts to dominate.
2. Re-run with a 500-residue sequence and watch the gap between 8M
   and 650M widen — the attention term hurts the smaller model
   proportionally less, but the larger model's better predictions
   start paying off more clearly.
3. Mask 5 different positions across the sequence and report the top-1
   recovery rate for each model. The 8M typically gets 1-2 of 5
   correct; the 650M gets 4-5 of 5; the 3B is usually 5/5.
4. If you have access to an 80 GB A100/H100, drop the try/except and
   actually time the 15B model. The forward-pass time vs. parameter
   curve usually extrapolates cleanly to the 15B point.

Next module: ESM3 multimodal — sequence + structure + function in one
transformer.
