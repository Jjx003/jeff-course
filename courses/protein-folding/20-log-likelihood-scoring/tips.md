## Hints

1. Loading the model and tokenizer (same HuggingFace stack as module 11):

```python
from transformers.utils import logging as hf_logging
hf_logging.set_verbosity_error()

import torch
from transformers import AutoTokenizer, EsmForMaskedLM

CHECKPOINT = "facebook/esm2_t33_650M_UR50D"
tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
model = EsmForMaskedLM.from_pretrained(CHECKPOINT)
model.eval()
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.half().to(device) if device == "cuda" else model.to(device)  # FP16 on GPU saves memory
```

2. Apply a mutation by index (1-indexed for human readability):

```python
def apply_mutation(seq: str, position_1based: int, new_aa: str) -> str:
    return seq[:position_1based - 1] + new_aa + seq[position_1based:]
```

3. Score one sequence by masking each position one at a time. The
   trick: tokenise the sequence once, then loop over positions and
   poke `tokenizer.mask_token_id` into the tensor at each step:

```python
import torch.nn.functional as F

def pll(model, tokenizer, sequence: str, device: str) -> float:
    mask_id = tokenizer.mask_token_id
    inputs = tokenizer(sequence, return_tensors="pt").to(device)
    token_ids = inputs["input_ids"]
    L = len(sequence)
    log_prob_sum = 0.0
    for i in range(L):
        masked = token_ids.clone()
        masked[0, i + 1] = mask_id  # +1 for the leading <cls>
        with torch.inference_mode():
            logits = model(input_ids=masked).logits
        log_probs = F.log_softmax(logits[0, i + 1].float(), dim=-1)
        true_token_id = token_ids[0, i + 1].item()
        log_prob_sum += float(log_probs[true_token_id].item())
    return log_prob_sum
```

Notes:

- `i + 1` in the indexing accounts for the leading `<cls>` token
  that ESM-2 prepends.
- We `.float()` the logits before `log_softmax` because FP16
  log-softmax can underflow for the smaller probabilities.
- `torch.inference_mode()` disables autograd entirely — without it
  you'd accumulate gradient state across all $L$ forward passes and
  OOM quickly. Use this instead of `torch.no_grad()` when you don't
  need a backward pass.

4. Build the full table by looping over wild-type and each mutant:

```python
mutations = [
    ("W8A", 8, "A"),
    ("W15A", 15, "A"),
    ("K17R", 17, "R"),
    ("A20V", 20, "V"),
]

variants = [("WT", WILD_TYPE)]
for name, pos, new_aa in mutations:
    variants.append((name, apply_mutation(WILD_TYPE, pos, new_aa)))

scores = {}
for name, seq in variants:
    scores[name] = pll(model, tokenizer, seq, device)
```

5. Pretty-print the results:

```python
wt_pll = scores["WT"]
print()
for name, _ in variants:
    p = scores[name]
    if name == "WT":
        print(f"  {name:6s} PLL = {p:.3f}")
    else:
        print(f"  {name:6s} PLL = {p:.3f}   delta = {p - wt_pll:+7.3f}")

print()
print("Ranking (most likely first):")
for rank, (name, _) in enumerate(sorted(variants, key=lambda v: -scores[v[0]]), start=1):
    print(f"  {rank}. {name:8s} PLL = {scores[name]:.3f}")
```

## CPU fallback

ESM-2 650M on CPU at FP32 takes ~30 s per forward pass. For 5
sequences × 30 positions = 150 forward passes, that's ~75 minutes.
If you're CPU-only and patient, replace `model.half().to(device)`
with `model.to(device)` (FP32 is more accurate on CPU).

If you don't want to wait, switch the `CHECKPOINT` to
`"facebook/esm2_t6_8M_UR50D"` (the smallest ESM-2, ~30 MB), which
runs in seconds on CPU. The PLL ranking will be qualitatively similar
but absolute numbers are different (smaller model, smaller context
window of learned co-evolution).

## Sanity checks

- The number of forward passes should be exactly $5 \times 30 = 150$.
- For all four mutants, $\Delta\text{PLL}$ should be **negative** (any random
  mutation is more likely to hurt than help under a fitness-style
  prior).
- `W8A` and `W15A` should have the largest negative $\Delta\text{PLL}$
  (typically $-10$ to $-20$). Tryptophan-at-conserved-position is
  hard to substitute.
- `K17R` should have the smallest magnitude $\Delta\text{PLL}$ (a few
  units). K and R are interchangeable in many contexts.
- Wild-type PLL on a 30-mer is typically $-30$ to $-60$ in absolute
  units. If you see $+1000$ or $-10000$, you've forgotten to take
  log-softmax (or are summing logits directly).

## Going deeper

- **Meier et al, 2021** — *Language models enable zero-shot prediction of the effects of mutations on protein function* — [https://www.biorxiv.org/content/10.1101/2021.07.09.450648v1](https://www.biorxiv.org/content/10.1101/2021.07.09.450648v1). The ESM-1v paper. Establishes PLL as a zero-shot variant-effect predictor.
- **Hopf et al, 2017** — *Mutation effects predicted from sequence co-variation* — [https://www.nature.com/articles/nbt.3769](https://www.nature.com/articles/nbt.3769). The EVmutation paper. The earlier MSA-based approach that PLL competes with.
- **Riesselman et al, 2018** — *Deep generative models of genetic variation capture the effects of mutations* — [https://www.nature.com/articles/s41592-018-0138-4](https://www.nature.com/articles/s41592-018-0138-4). DeepSequence; per-protein VAEs as a fitness proxy.
- **Wang & Cho, 2019** — *BERT has a Mouth, and It Must Speak: BERT as a Markov Random Field Language Model* — [https://aclanthology.org/W19-2304/](https://aclanthology.org/W19-2304/). Theoretical justification for PLL on MLMs.
- **ProteinGym benchmark** — [https://www.proteingym.org/](https://www.proteingym.org/). Standardised evaluation suite for variant-effect predictors. ESM-1v, ESM-2, ESM-IF1, AlphaFold2, etc all evaluated head-to-head.

## Things to try after

1. **Compute PLL with ESM-2 8M instead.** Smaller model, faster
   inference, but lower correlation with assay data. Compare the
   ranking of the 4 variants.
2. **Restrict the softmax to the 20 canonical AAs** before
   log-softmax. Compare to the full-vocabulary version. The
   ranking should be identical; the absolute PLL values shift by a
   small constant.
3. **Try multi-mutant.** Apply both `W8A` and `W15A` to the same
   sequence and compute PLL. Compare $\Delta\text{PLL}$ to the sum
   of the individual deltas. The difference is a measure of
   epistasis (under PLL).
4. **Cache WT logits.** For each single-point mutant, only the
   masked position $i$ contributes a different log-probability —
   the other 29 positions give the same value as WT. Implement the
   one-shot version and compare runtime.
5. **Random-subset masking.** Mask 10% of positions per forward
   pass, run 10 passes total. Compare to the strict per-position
   PLL. You should see most of the signal at a fraction of the
   compute.

Next module: inverse folding with ProteinMPNN — given a backbone,
sample plausible sequences that could fold into it.
