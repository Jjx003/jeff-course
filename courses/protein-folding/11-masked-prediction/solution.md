## Walkthrough

### Loading the model

```python
from transformers import AutoTokenizer, EsmForMaskedLM

CHECKPOINT = "facebook/esm2_t33_650M_UR50D"
tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
model = EsmForMaskedLM.from_pretrained(CHECKPOINT)
model.eval()
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
```

`AutoTokenizer` returns the right tokenizer class for the checkpoint
(`EsmTokenizer` here). `EsmForMaskedLM` is the wrapper that bundles
the encoder stack with the language-model head — exactly what we
want for masked-token prediction.

`from_pretrained` handles weight downloading automatically — first
call fetches ~2.6 GB from the HuggingFace Hub, subsequent calls reuse
the cached file in `~/.cache/huggingface/hub/`.

`model.eval()` disables dropout. For pure inference the difference is
small (no stochastic regularisation paths active anyway), but it's
the canonical PyTorch idiom and should always be present in
inference scripts.

### The mask trick

```python
inputs = tokenizer(SEQUENCE, return_tensors="pt").to(device)
mask_token_idx = MASK_POS_1BASED   # 1-based residue idx == 0-based token idx after <cls>
inputs["input_ids"][0, mask_token_idx] = tokenizer.mask_token_id
```

There are two equivalent ways to insert a `<mask>` token:

1. **In-place tensor edit** (used here). Tokenize the full sequence,
   then overwrite one token in `input_ids` with the mask ID. No
   string parsing.
2. **String substitution.** Build `SEQUENCE[:13] + "<mask>" +
   SEQUENCE[14:]` and pass it through the tokenizer; the
   ESM tokenizer treats `<mask>` as a single special token.

We use option 1 because it never depends on the tokenizer's special-
token-parsing rules — useful when adapting this code to other
checkpoints.

After tokenization the input layout is:

```
input_ids = [<cls>, M, G, L, S, D, G, E, W, Q, L, V, L, N, <mask>, W, G, K, ..., <eos>]
indices     0      1  2  3  4  5  6  7  8  9 10 11 12 13 14       15 16 17       L+1
```

The mask token sits at token index 14 (1-based residue index 14, plus
1 for `<cls>` minus 1 for the residue we replaced).

### Forward pass and logit extraction

```python
with torch.inference_mode():
    out = model(**inputs)
logits = out.logits[0, MASK_POS_1BASED]   # shape (V,) = (33,)
```

`out.logits` has shape `(batch, seq_len, vocab)`. We grab batch
element 0, token index `MASK_POS_1BASED`. The result is a 33-entry
logit vector — one entry per token in ESM-2's vocab.

`torch.inference_mode()` is the recommended idiom for forward-only
PyTorch in 2024+. It's a strict superset of `torch.no_grad()` and is
slightly faster.

### Filtering to amino acids

```python
aa_token_ids = torch.tensor(
    [tokenizer.convert_tokens_to_ids(c) for c in AA_LETTERS],
    device=device,
)
aa_logits = logits[aa_token_ids]
aa_probs = torch.softmax(aa_logits, dim=-1)
```

ESM-2's vocabulary has 33 entries (20 amino acids + 13 special and
ambiguity tokens). For pedagogical purposes we only care about the
20 amino-acid predictions. Selecting them and applying softmax to
the slice gives a 20-class distribution.

A more principled alternative: softmax over the full vocab, then
slice. Mathematically these are different — full-vocab softmax keeps
some probability "lost" on non-amino-acid tokens — but in practice
the model concentrates almost all probability on amino-acid tokens
anyway, so the two approaches agree to ~3 decimal places.

### Top-5

```python
topk = torch.topk(aa_probs, k=5)
for prob, idx in zip(topk.values.tolist(), topk.indices.tolist()):
    letter = AA_LETTERS[idx]
    print(f"  {letter}    p={prob:.4f}")
```

`torch.topk` returns `(values, indices)`. The indices index into
`AA_LETTERS` since we restricted the logits to that 20-letter
vocabulary first.

## Reading the model's answer

For position 15 (the `W` of the conserved `WGK` motif), ESM-2 650M's
typical output looks like:

```
W    p=0.7421
Y    p=0.0834
F    p=0.0612
H    p=0.0298
L    p=0.0151
```

(Exact numbers depend on the version of `transformers` and PyTorch —
they won't be byte-identical between runs, which is why this module
returns a `pending` verdict instead of being graded.)

Two notable patterns:

- **W dominates with > 70 % probability.** The model has memorised
  that this position is a conserved aromatic in globin sequences —
  exactly the signal an MSA + conservation analysis (module 7) would
  surface.
- **The runners-up are chemically related.** `Y` and `F` are also
  aromatic. `H` is an aromatic-ish polar that occasionally
  substitutes in evolution. `L` is a hydrophobic that can plausibly
  fill an aromatic pocket.

This is the BLOSUM62-on-steroids behaviour from module 10, made
concrete: the model has learned that `W` is uniquely conserved here
and that the closest substitutions are aromatic / hydrophobic.

## Why doesn't the model just memorise the answer?

A reasonable worry: maybe `MGLSDGEWQLVLNVWGKVEADIPGHGQEVL` (the human
myoglobin N-terminal fragment) is in the training set, so the model
is just reciting the answer.

The MLM objective forces the model to predict each masked position
*from context*. Even if the exact sequence was in the training set,
during training the model would have seen this position with
`<mask>` at the relevant slot — so the gradient signal trains it to
infer `W` from the context, not memorise it as a known answer.

A more rigorous evaluation: take a *novel* sequence, mask a position,
and predict. Module 20 does exactly this on user-provided variants.

## What if the top-1 doesn't match?

Sometimes the top-1 prediction differs from the original residue.
Two possible reasons:

1. **The position is genuinely ambiguous in evolution.** A surface
   loop residue might honestly have multiple equally-likely
   substitutions from the model's perspective.
2. **The original sequence is unusual.** If the wild-type happens to
   have a rare residue at this position, the model — trained on the
   broader distribution — predicts the more common substitution.

Either case is informative: the model is telling you something about
how unusual the wild-type residue is in its evolutionary context.

## Connection to the next modules

- **Module 12** uses the same model but extracts the full per-residue
  embeddings (via `EsmModel`, no language-model head) instead of the
  logit head's predictions.
- **Module 13** swaps in different ESM-2 sizes and shows that the
  top-1 confidence sharpens with scale.
- **Module 20** generalises the masking trick to compute pseudo-log-
  likelihood across an entire sequence, turning ESM-2 into a
  zero-shot variant-effect predictor.
