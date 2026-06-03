## Hints

1. Suppress noisy load logs so they don't interleave with your output:

```python
from transformers.utils import logging as hf_logging
hf_logging.set_verbosity_error()
```

2. Loading the tokenizer and model:

```python
import torch
from transformers import AutoTokenizer, EsmForMaskedLM

CHECKPOINT = "facebook/esm2_t33_650M_UR50D"
tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
model = EsmForMaskedLM.from_pretrained(CHECKPOINT)
model.eval()

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
```

`model.eval()` disables dropout — strictly necessary for reproducible
inference. `EsmForMaskedLM` is the wrapper that exposes the
language-model head; `EsmModel` would skip the head and only return
hidden states (we use that for embeddings in module 12).

3. Constructing the masked input. The cleanest way is to tokenize the
   unmasked sequence, then overwrite one token in-place with
   `tokenizer.mask_token_id`:

```python
SEQUENCE = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"
mask_pos_1based = 15
original_residue = SEQUENCE[mask_pos_1based - 1]   # 'W'

inputs = tokenizer(SEQUENCE, return_tensors="pt").to(device)
mask_token_idx = mask_pos_1based   # 1-based residue idx == 0-based token idx after <cls>
inputs["input_ids"][0, mask_token_idx] = tokenizer.mask_token_id
```

(An alternative is to assemble a string with a literal `<mask>`
substring — `SEQUENCE[:14] + "<mask>" + SEQUENCE[15:]` — and let the
tokenizer parse it. Both work; the in-place overwrite approach uses
no string parsing and never needs you to remember whether
`<mask>` is treated as a single token.)

4. Forward pass under `torch.inference_mode()`:

```python
with torch.inference_mode():
    out = model(**inputs)
logits = out.logits          # shape (1, L+2, V)
position_logits = logits[0, mask_token_idx]   # shape (V,)
```

`torch.inference_mode()` is the modern replacement for
`torch.no_grad()` and is slightly faster — it disables both gradient
tracking and autograd version counters. Either is fine for this
exercise.

5. Top-5 over amino-acid tokens only. ESM-2's vocab includes
   non-residue tokens; filter them out:

```python
AA_LETTERS = "ACDEFGHIKLMNPQRSTVWY"
aa_token_ids = torch.tensor(
    [tokenizer.convert_tokens_to_ids(aa) for aa in AA_LETTERS],
    device=device,
)
aa_logits = position_logits[aa_token_ids]
aa_probs = torch.softmax(aa_logits, dim=-1)

topk = torch.topk(aa_probs, k=5)
for prob, idx in zip(topk.values.tolist(), topk.indices.tolist()):
    print(f"  {AA_LETTERS[idx]}    p={prob:.4f}")
```

(Alternatively, take softmax over the full vocab and then index;
either works, but restricting to amino acids first is slightly more
interpretable.)

6. Comparing top-1 to original:

```python
top1_letter = AA_LETTERS[topk.indices[0].item()]
print(f"Top-1 matches original ('{original_residue}'): {top1_letter == original_residue}")
```

## CPU fallback

If your machine has no GPU, the script auto-detects and runs on CPU.
Expect 10–30 seconds for the full forward pass on a 30-residue
sequence. Anything noticeably longer suggests the model is being
recomputed on every call — make sure you load it once outside any
loops.

## Sanity checks

- `inputs["input_ids"].shape == (1, len(SEQUENCE) + 2)` — one batch,
  length plus `<cls>` plus `<eos>`.
- After overwrite, `inputs["input_ids"][0, mask_token_idx].item() ==
  tokenizer.mask_token_id`. Print and confirm.
- `aa_probs.sum()` should be exactly 1.0 (it's a softmax over 20
  classes).
- The top-1 prediction for a masked `W` in a globin context should be
  `W` (different ESM-2 sizes give slightly different runner-up lists,
  but `W` consistently wins).
- Top-5 probabilities should sum to > 0.9 for a confident position.
- For a less-conserved position (e.g. mask `D` at position 5), the
  top-5 distribution is much flatter — that's the model honestly
  saying "this position is variable in the training distribution".

## Going deeper

- **Lin et al, 2023** — *Evolutionary-scale prediction of atomic-level protein structure* — [https://www.science.org/doi/10.1126/science.ade2574](https://www.science.org/doi/10.1126/science.ade2574). The ESM-2 / ESMFold paper. Includes the empirical demonstration that scaling MLM training to 15B parameters produces structure-quality predictions without MSA search.
- **Rives et al, 2019** — *Biological structure and function emerge from scaling unsupervised learning to 250 million protein sequences* — [https://www.biorxiv.org/content/10.1101/622803](https://www.biorxiv.org/content/10.1101/622803). The original ESM-1 paper, which first showed that PLM embeddings encode structural information.
- **HuggingFace ESM-2 model card** — [https://huggingface.co/facebook/esm2_t33_650M_UR50D](https://huggingface.co/facebook/esm2_t33_650M_UR50D). Weights, config, tokenizer JSON. Also lists every other ESM-2 size.
- **`transformers` ESM source** — [https://github.com/huggingface/transformers/tree/main/src/transformers/models/esm](https://github.com/huggingface/transformers/tree/main/src/transformers/models/esm). The model + tokenizer implementation, ~1.5K lines of clean PyTorch.
- **`fair-esm` GitHub** — [https://github.com/facebookresearch/esm](https://github.com/facebookresearch/esm). Meta's original release, in case you want to compare APIs or use the contact-prediction wrapper.
- **Meier et al, 2021** — *Language models enable zero-shot prediction of the effects of mutations on protein function* — [https://www.biorxiv.org/content/10.1101/2021.07.09.450648](https://www.biorxiv.org/content/10.1101/2021.07.09.450648). Uses the same masked-prediction probabilities as a zero-shot variant-effect predictor — directly relevant to module 20.

## Things to try after

1. Mask a different position. Try a conserved hydrophobic core
   residue (`L` or `V` in the sequence) vs a surface residue (`E` or
   `K`). Compare top-5 sharpness.
2. Mask **multiple** positions at once. Replace several token IDs
   with `tokenizer.mask_token_id`, run forward, and read the top-5
   for each. Note that the model still treats them as conditionally
   independent given the rest of the sequence.
3. Score a known mutant. Compute the probability of the wild-type
   letter vs the mutant letter at a single masked position. The
   *log-probability ratio* is a single-position approximation to a
   "fitness change" — module 20 turns this into a full PLL pipeline.
4. Compare ESM-2 sizes. Module 13 spells this out, but you can
   preview by swapping `t33_650M` for `t6_8M` and watching the top-5
   list become noticeably less confident.
