## Hints

1. Suppress HuggingFace's noisy load logging at the top of your script
   so the diff against `expected_output/python.txt` doesn't fail on a
   stray warning:

```python
from transformers.utils import logging as hf_logging
hf_logging.set_verbosity_error()
```

2. Loading the tokenizer:

```python
from transformers import AutoTokenizer
CHECKPOINT = "facebook/esm2_t6_8M_UR50D"
tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
```

`tokenizer.vocab_size` should be `33`. The five special-token IDs
live at `tokenizer.cls_token_id`, `tokenizer.pad_token_id`,
`tokenizer.eos_token_id`, `tokenizer.unk_token_id`,
`tokenizer.mask_token_id`.

3. Encoding a sequence:

```python
out = tokenizer("MGLSDGEW")
ids = out["input_ids"]   # plain Python list when no return_tensors arg
```

This wraps the sequence with `<cls>` and `<eos>` automatically, so
the result has length `len(seq) + 2`. To get just the per-residue
IDs (without specials), pass `add_special_tokens=False`.

4. Loading the model and grabbing its embedding matrix:

```python
import torch
from transformers import EsmModel

model = EsmModel.from_pretrained(CHECKPOINT)
model.eval()

embedding_matrix = model.embeddings.word_embeddings.weight    # (33, 320)
```

The `.eval()` call disables dropout. We won't run a forward pass in
this module — we only read the embedding matrix — so this is mainly
good practice for the modules that come after.

5. Looking up a residue's embedding:

```python
m_id = tokenizer.convert_tokens_to_ids("M")    # 20
m_vec = embedding_matrix[m_id]                 # shape (320,)
```

The matrix is a `torch.nn.Parameter`, which is a `torch.Tensor`. Use
`.tolist()` and `float(...)` to get plain Python numbers for
formatting.

6. Output formatting. The expected lines for "first 4 values" and
   "last 4 values" use 4 decimal places inside square brackets:

```python
def fmt_list(values) -> str:
    return "[" + ", ".join(f"{x:.4f}" for x in values) + "]"

print(f"  first 4 values: {fmt_list(m_vec[:4].tolist())}")
print(f"  last 4 values: {fmt_list(m_vec[-4:].tolist())}")
print(f"  sum of all 320 values: {float(m_vec.sum()):.4f}")
```

The "Per-residue IDs" lines are right-padded position numbers:
`f\"    pos {i:>2}  {aa} -> {tid}\"`.

## Sanity checks

- `tokenizer.vocab_size` must equal `33`. If you're seeing a different
  number, you're loading a different tokenizer.
- `tokenizer.cls_token_id == 0`, `tokenizer.eos_token_id == 2`,
  `tokenizer.mask_token_id == 32`. If these don't match, you're
  loading something other than the standard ESM-2 tokenizer.
- The encoded length for "MGLSDGEW" must be exactly 10 (8 residues +
  `<cls>` + `<eos>`).
- The token IDs must be `[0, 20, 6, 4, 8, 13, 6, 9, 22, 2]`. ESM-2's
  amino-acid order is *not* alphabetical — `M` is `20`, not `15` like
  it would be in a naive A-Z mapping.
- The embedding matrix shape is `(33, 320)` for ESM-2 8M. Bigger
  ESM-2 sizes have the same vocab (33) but wider embeddings (480,
  640, 1280, 2560, 5120).

## Going deeper

- **HuggingFace ESM-2 model card** — [https://huggingface.co/facebook/esm2_t6_8M_UR50D](https://huggingface.co/facebook/esm2_t6_8M_UR50D). Tokenizer, vocab JSON, all six ESM-2 sizes.
- **Lin et al, 2023** — *Evolutionary-scale prediction of atomic-level protein structure* — [https://www.science.org/doi/10.1126/science.ade2574](https://www.science.org/doi/10.1126/science.ade2574). The ESM-2 + ESMFold paper.
- **Vaswani et al, 2017** — *Attention Is All You Need* — [https://arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762). The original transformer paper, including the sinusoidal positional-encoding formulation.
- **Su et al, 2021** — *RoFormer: Enhanced Transformer with Rotary Position Embedding* — [https://arxiv.org/abs/2104.09864](https://arxiv.org/abs/2104.09864). The RoPE paper. ESM-2 and most modern transformers use RoPE.
- **`fair-esm` GitHub** — [https://github.com/facebookresearch/esm](https://github.com/facebookresearch/esm). Meta's original ESM release. Includes the `Alphabet` class and `BatchConverter` if you ever need to compare APIs.
- **Karpathy's Zero-to-Hero playlist** — [https://karpathy.ai/zero-to-hero.html](https://karpathy.ai/zero-to-hero.html). The "Build GPT from scratch" lectures cover tokenization, embeddings, and positional encodings in delightful detail.

## Things to try after

1. Tokenize a longer sequence with non-canonical residues (e.g.
   `"MGLSDGEWXBO"`). Confirm that `X`, `B`, `O` get their own integer
   IDs (24, 25, 28) rather than collapsing to `<unk>`.
2. Compare embeddings across amino acids. Compute the cosine
   similarity between the embeddings of `L` and `I` (both
   hydrophobic) vs `L` and `D` (hydrophobic vs charged). The
   hydrophobic pair should be noticeably closer — exactly the
   "BLOSUM-like" structure module 10 will discuss.
3. Run a full forward pass and look at the difference between
   `inputs_embeds` (just the lookup we did here) and the final-layer
   `last_hidden_state`. Module 12 will do exactly this.

Next module: a reading-only deep dive that re-frames encoder
transformers as continuous, learned fuzzy string matching — the
mental model that makes everything from module 11 onwards click.
