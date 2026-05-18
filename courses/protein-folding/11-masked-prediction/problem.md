## Goal

Load **ESM-2 650M** (the 33-layer version of Meta AI's protein
language model) from the HuggingFace Hub, mask out one residue in a
short sequence, run a forward pass, and print the model's top-5
predictions for the masked position with their probabilities.

This is the simplest possible demonstration that a pretrained PLM has
absorbed something biologically meaningful into its weights. If the
training-time MLM objective worked, the model should refill a masked
residue with a chemically reasonable letter — often the same letter
that was originally there, since the model has implicitly learned
sequence statistics over hundreds of millions of UniRef proteins.

## Hardware

- **Recommended:** an NVIDIA GPU with $\ge 6\ \text{GB}$ VRAM. The
  650M-parameter model weights are ~2.6 GB in FP32 and ~1.3 GB in
  FP16. Inference for a 30-residue sequence is essentially instant on
  any modern card.
- **Acceptable:** CPU. The forward pass takes ~10–30 seconds on a
  typical laptop. The script picks `cpu` automatically if no CUDA
  device is available.

The platform doesn't grade exact probabilities (they're
hardware/version sensitive), so this module returns a `pending`
verdict. Run it locally and inspect the output yourself.

## The exercise

1. Load the tokenizer and model from
   `facebook/esm2_t33_650M_UR50D` using HuggingFace `transformers`.
2. Use the **MB fragment** from module 6:

   ```text
   MGLSDGEWQLVLNVWGKVEADIPGHGQEVL
   ```

3. Mask **position 14** (1-based; the `W` of the conserved `WGK`
   motif). Replace it with the model's `<mask>` token before the
   forward pass.
4. Run the model under `torch.inference_mode()` and grab the logits at
   the masked position.
5. Convert the logits to probabilities with `softmax`, restrict to
   the 20 standard amino acids, take the top-5, and print:
   - The original residue at the position.
   - The model's top-5 predicted amino acids and their probabilities.
   - Whether the model's top-1 prediction matches the original residue.

## Tokenization details

The HuggingFace `EsmTokenizer` for ESM-2 produces:

```python
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("facebook/esm2_t33_650M_UR50D")
out = tokenizer("MGLSDGEW", return_tensors="pt")
# out["input_ids"] has shape (1, L+2): [<cls>, x_1, ..., x_L, <eos>]
# out["attention_mask"] has shape (1, L+2)
```

`tokenizer.mask_token_id` is the integer ID for `<mask>` (32 for
ESM-2). To insert the mask, the cleanest approach is to tokenize the
unmasked sequence and overwrite the target token in-place:

```python
inputs = tokenizer(SEQUENCE, return_tensors="pt")
mask_token_idx = MASK_POS_1BASED   # 1-based residue idx == token idx after <cls>
inputs["input_ids"][0, mask_token_idx] = tokenizer.mask_token_id
```

The `+1` for `<cls>` and the `+0` for the mask cancel out — a
1-based residue position equals the 0-based token index it lives at.

## Expected output (illustrative)

The exact probabilities depend on PyTorch / `transformers` versions
and on whether the model runs in FP32 vs FP16 — so the platform
doesn't grade them. A correct run prints something like:

```text
Loading facebook/esm2_t33_650M_UR50D ...
Model loaded. Parameters: 651,765,793
Running on: cuda

Sequence (length 30):
MGLSDGEWQLVLNVWGKVEADIPGHGQEVL

Masking position 14 (1-based, original residue 'W'):
MGLSDGEWQLVLN<mask>WGKVEADIPGHGQEVL

Top-5 predicted amino acids for the masked position:
  W    p=0.7421
  Y    p=0.0834
  F    p=0.0612
  H    p=0.0298
  L    p=0.0151

Top-1 matches original ('W'): True
```

Two things to notice:

- The top-1 prediction is overwhelmingly the original `W`. The model
  has implicitly learned that the `WGK` motif is highly conserved in
  globin sequences, and it's confident.
- The runners-up are mostly *aromatic / hydrophobic* (Y, F, H) — the
  model is suggesting chemically similar substitutions, exactly what
  the learned BLOSUM-style similarity function from module 10 should
  do.

## What you should learn

- **Loading a 650M-parameter model is two lines** with HuggingFace
  `transformers`. `AutoTokenizer` and `EsmForMaskedLM` hide all the
  complexity.
- **MLM inference is "compute logits, softmax, top-k".** The
  innovation is in the *training*, not the *inference*.
- **The model's predictions are biologically sensible.** The fact
  that it suggests `W → W/Y/F/H` for a conserved aromatic position
  is concrete evidence that the compressed-database story from
  module 10 is real.
- **You can do this entirely offline once the weights are downloaded.**
  No internet calls during inference. ESM-2 650M is a static
  computation.

The next module turns this around: instead of reading prediction
probabilities, we'll extract the per-residue *embeddings* and use
them as a similarity measure (module 12).
