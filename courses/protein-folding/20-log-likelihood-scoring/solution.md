## Walkthrough

### Tokenisation and the leading `<cls>` offset

```python
inputs = tokenizer(sequence, return_tensors="pt").to(device)
token_ids = inputs["input_ids"]
```

The HuggingFace `EsmTokenizer` returns a dict whose `input_ids`
tensor has shape `(1, L + 2)` with layout
`[<cls>, t_1, ..., t_L, <eos>]`. So when we want to mask the $i$-th
*amino acid* (0-indexed), the corresponding token-tensor index is
`i + 1`.

### The masking loop

```python
for i in range(L):
    masked = token_ids.clone()
    masked[0, i + 1] = mask_id
    with torch.inference_mode():
        logits = model(input_ids=masked).logits
    log_probs = F.log_softmax(logits[0, i + 1].float(), dim=-1)
    true_token_id = token_ids[0, i + 1].item()
    log_prob_sum += float(log_probs[true_token_id].item())
```

Five things to notice:

1. `token_ids.clone()` — we need a fresh copy at every step or we'd
   accumulate masks.
2. `masked[0, i + 1] = mask_id` — change one position at a time.
   `mask_id = tokenizer.mask_token_id` is the integer ID of the
   `<mask>` token (32 in ESM-2's vocabulary).
3. `torch.inference_mode()` — disables autograd entirely; faster
   than `torch.no_grad()` and avoids OOM-via-saved-activations
   across the loop.
4. `logits[0, i + 1].float()` — pull out the logit row for the
   masked position and upcast to FP32 before log-softmax. The
   `.float()` is crucial in FP16 inference; without it, log_softmax
   can underflow for low-probability classes.
5. `log_probs[true_token_id].item()` — index into the log-probability vector with the *true* token (the one we masked) to get the model's predicted probability for it.

### Total PLL

```python
return log_prob_sum
```

The sum across all $L$ positions. For our 30-mer, this is a sum of
30 terms, each in roughly $[-5, 0]$ range (most positions are highly
predictable; some are uncertain).

### Per-mutant scoring

```python
for name, seq in variants:
    scores[name] = pll(model, tokenizer, seq, device)
```

We call `pll` on each variant. For a single-point mutation, the WT
and mutant differ in only one residue, but the PLL of the mutant is
re-computed from scratch — the model evaluates 30 conditionals for
each. A more efficient implementation caches the WT logits and only
re-evaluates the mutated position.

## Why W8A and W15A score so much worse

Tryptophan is the rarest amino acid (~1 % in proteins) and the most
expensive to make. Where it appears, it's usually structurally
crucial: aromatic stacking, hydrophobic core anchors, or specific
binding pockets. ESM-2 has seen that pattern across millions of
training sequences.

When we mask `W15` and ask "what residue is most likely here?", the
model returns:

- W: ~0.7
- F (phenylalanine): ~0.15
- Y (tyrosine): ~0.10
- L (leucine): ~0.03
- everything else: < 1% combined

So `log p(W | masked) ≈ log(0.7) ≈ -0.36`.

For the W15A mutant, we ask "what residue is most likely at
position 15?" — and the model still wants W:

- W: 0.7, A: 0.005

So `log p(A | masked) ≈ log(0.005) ≈ -5.3`.

The PLL difference at this single position alone: about $-5$. The
delta over all 30 positions is mostly this term plus secondary
effects — the masked position's neighbours in the model's
context-aware scoring may also shift slightly.

For W8A you get a similar ~$-10$ to $-15$ unit drop because both
tryptophans are highly conserved.

## Why K17R is nearly neutral

Lysine and arginine are both positively charged at physiological pH
and are routinely substituted for each other in evolution. The
model has seen "K or R" substitutions on the order of millions of
times in its training corpus. Predictions:

- K: 0.4, R: 0.3, others combined: 0.3

So `log p(K | masked) ≈ -0.92`, and `log p(R | masked) ≈ -1.20`.

The PLL difference at the position is only ~$-0.3$. The full
$\Delta\text{PLL}$ rarely exceeds 1-2 units for conservative
substitutions.

## Why FP16 is fine here

PLL is a **difference** between sequences. Any consistent FP16
quantisation noise affects WT and mutant equally, so $\Delta\text{PLL}$
is preserved. For absolute PLL values, FP16 gives slightly less
accurate numbers than FP32, but both rank the variants the same way.

## Cost analysis

For the 30-residue sequence and 5 variants, total cost on a
typical GPU:

- 5 sequences × 30 positions = 150 forward passes.
- Each forward pass on ESM-2 650M (FP16, batch 1, length 32) is
  ~30-50 ms on an RTX 3090.
- Total: ~5-8 seconds wall-clock for inference; another few
  seconds for model load.

Scaling: for a 1000-residue protein and 50 mutants, you'd need
50000 forward passes — about an hour. For a real Cradle-style
library of $10^4-10^6$ variants, this is the bottleneck that
motivates the WT-cache optimisation described in tips.md.

## Connection to module 22

Cradle's "logiter" pipeline is essentially this script + an
evotuning step:

1. Take ESM-2.
2. Fine-tune (evotune) on an MSA of the target protein family.
3. Use the fine-tuned model's PLL as the initial fitness predictor.
4. Combine with a regression head trained on assay data
   (g-DPO / supervised fitness prediction).
5. Rank variants by the combined score; select top-K for wet lab.

The PLL we computed here is step 3 with **no** evotuning — pure
zero-shot ESM-2. Cradle's claim is that this baseline already
correlates with fitness, and the rest of the pipeline tightens the
correlation.

## Going beyond this module

For real projects:

- **Cache wild-type logits.** Compute WT PLL once, then only
  re-evaluate the mutated position(s) for each mutant. Speedup:
  $L\times$ for single-point mutations.
- **Batch across variants.** Mask the same position $i$ across
  multiple sequences in one forward pass. Memory-bound but
  $4-8\times$ throughput improvement.
- **Use ESM-1v** (`esm1v_t33_650M_UR90S_1` through `_5`) instead.
  These are ESM models specifically trained for variant effect
  prediction; they don't include `<mask>` in their vocabulary, and
  use a slightly different masking scheme. Often score better than
  ESM-2 for variant ranking (Meier et al, 2021).
- **Compare to AlphaFold-based fitness scores.** AlphaFold2 also
  has a "predicted fitness" mode via $\Delta\text{pLDDT}$. PLL is
  cheaper and often comparable.

Next module — module 21 — flips the problem: given a backbone
structure, sample sequences that could fold into it. Inverse
folding with ProteinMPNN.
