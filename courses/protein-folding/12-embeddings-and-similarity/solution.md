## Walkthrough

### Embedding helper

```python
@torch.inference_mode()
def embed(seq: str) -> torch.Tensor:
    inputs = tokenizer(seq, return_tensors="pt").to(device)
    outputs = model(**inputs)
    reps = outputs.last_hidden_state[0, 1 : 1 + len(seq)]
    return reps.cpu().float()
```

Three subtleties:

- `EsmModel` (rather than `EsmForMaskedLM`) returns hidden states
  without the LM head — exactly what we want for embedding extraction.
- `torch.inference_mode()` is slightly cheaper than `torch.no_grad()`
  for pure inference and is the recommended default in modern PyTorch.
- `[0]` indexes batch element 0; `[1 : 1 + len(seq)]` strips off the
  `<cls>` (token index 0) and `<eos>` (token index `len(seq) + 1`),
  leaving an `(L, 1280)` per-residue tensor.

### L2 normalisation

```python
mb_n = F.normalize(mb_emb, dim=-1)
hbb_n = F.normalize(hbb_emb, dim=-1)
```

`F.normalize` divides each row by its L2 norm. After this, every row
of `mb_n` has unit length, so `mb_n @ hbb_n.T` directly gives cosine
similarities.

### The single-matmul similarity matrix

```python
sim = mb_n @ hbb_n.T   # (30, 1280) @ (1280, 31) -> (30, 31)
```

This is the entire cross-similarity matrix in one operation. Compare
to the explicit double-loop version:

```python
sim = torch.zeros(len(MB), len(HBB))
for i in range(len(MB)):
    for j in range(len(HBB)):
        sim[i, j] = (mb_n[i] @ hbb_n[j])
```

— functionally identical, ~1000× slower. The single-matmul form is
also what the GPU is happiest with.

### Top-5 with flattened indexing

```python
flat = sim.flatten()
topk = torch.topk(flat, k=5)
i, j = divmod(idx, n_cols)
```

`torch.topk` only works on a single dimension at a time. Flattening
makes "find top-5 over the whole matrix" a 1-D problem; `divmod`
recovers the 2-D `(row, col)` coordinates.

## What you typically see

For ESM-2 650M on the MB / HBB N-terminal fragments, the top of the
list almost always includes:

- The conserved `W` of the `WGK` motif (cosine ~0.93).
- The `G` and `K` of the same motif (cosine ~0.88-0.92).
- A handful of conserved hydrophobic positions on either side of `WGK`.

The mean cross-similarity is in the range 0.55-0.65, which is
dramatically higher than the ~0.4 you'd see for two unrelated
proteins. This single number is a usable "how related are these two
proteins?" zero-shot score.

## Why "embedding cosine" works as a similarity score

Three accumulated reasons:

1. **MLM training pulls similar residues together.** During pretraining,
   gradients from the cross-entropy loss only descend if the model
   correctly predicts the masked residue from context. Two residues
   that play similar roles in similar contexts get similar
   "predictability profiles", which manifests as similar embedding
   directions.
2. **Attention is contextual averaging.** Each residue's embedding is
   formed by attending to its sequence context, so residues in
   similar surrounding contexts get similar embeddings. Conserved
   motifs are the most consistent contexts in the training data.
3. **The 1280-d space is overcomplete.** Every "feature" the model
   has learned has its own dimensions; cosine similarity in this
   space captures all of them at once, weighted equally. This is
   what makes it act like a "learned BLOSUM62".

## Connection to the rest of the course

- **Module 13** runs the masked-prediction sibling task at multiple
  model sizes; the same "scale sharpens the conserved-motif signal"
  story plays out, just in the logits over the masked position rather
  than in pairwise cosine similarities.
- **Module 17** uses the embedding similarity intuition to motivate
  ESMFold replacing the explicit MSA with implicit PLM patterns.
- **Module 22** uses pooled embeddings as the input to the
  *predictor* head in the Cradle pipeline — a direct application of
  PLM embeddings to lead optimisation.
