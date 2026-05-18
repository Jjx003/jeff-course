## Goal

Extract **per-residue embeddings** from ESM-2 650M for the two short
globin fragments from module 6, then compute the pairwise **cosine
similarity** between every cross-protein residue pair. Print the top-5
most-similar residue pairs.

Cosine similarity is the continuous, learned analogue of BLOSUM62
alignment scoring: instead of looking up a $20 \times 20$ table, we
compare two high-dimensional vectors that the model produced in
context. Module 10 argued that this is what attention's similarity
computation does internally; this module materialises the embeddings
and compares them directly.

## Sequences

Same fragments as module 6:

```text
MB_fragment : MGLSDGEWQLVLNVWGKVEADIPGHGQEVL  (30 residues, human myoglobin N-term)
HBB_fragment: VHLTPEEKSAVTALWGKVNVDEVGGEALGRL (31 residues, human haemoglobin beta N-term)
```

These are evolutionary cousins. They share the conserved `WGK` motif
that begins the E-helix in every globin, plus structural and
chemical similarity in much of the rest of the chain.

## The exercise

1. Load `EsmModel.from_pretrained("facebook/esm2_t33_650M_UR50D")`
   from HuggingFace `transformers` (no LM head — we only want hidden
   states) and run a forward pass on each sequence *separately*:

   ```python
   from transformers import AutoTokenizer, EsmModel

   tokenizer = AutoTokenizer.from_pretrained("facebook/esm2_t33_650M_UR50D")
   model = EsmModel.from_pretrained("facebook/esm2_t33_650M_UR50D")
   model.eval()

   inputs = tokenizer(seq, return_tensors="pt").to(device)
   with torch.inference_mode():
       out = model(**inputs)
   reps = out.last_hidden_state   # shape (1, L+2, 1280)
   ```

   The `+2` in `L+2` is the `<cls>` token prepended at index 0 and the
   `<eos>` token appended at index `L+1`.

2. Strip the `<cls>` and `<eos>` rows so you get a `(L, 1280)` tensor
   of per-residue embeddings for each sequence.

3. L2-normalise each embedding. Then the cosine similarity is just a
   dot product:

   $$\text{cos}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u}^\top \mathbf{v}}{\lVert \mathbf{u} \rVert \, \lVert \mathbf{v} \rVert}$$

4. Compute the cross-similarity matrix $S \in \mathbb{R}^{30 \times 31}$
   where $S_{ij}$ is the cosine similarity between residue $i$ of MB
   and residue $j$ of HBB.

5. Also compute a **single sequence-level cosine similarity** by
   mean-pooling each `(L, 1280)` tensor over the residue dim — averaging
   only over real residues, *not* including `<cls>` / `<eos>` — and then
   calling `torch.nn.functional.cosine_similarity` on the two pooled
   vectors.

6. Print:
   - The shape of each embedding tensor.
   - The shape of the cross-similarity matrix.
   - The mean / max / min cross-similarity (scalars — the mean should
     be modestly positive because both are globin fragments).
   - The sequence-level cosine similarity (a single scalar).
   - The **top 5 most-similar cross-protein residue pairs**, formatted
     as `MB[<i>]=<aa> HBB[<j>]=<aa> sim=<value>` (1-based positions).

## Expected output (illustrative)

The probabilities are model- and version-specific so the grader leaves
the verdict pending. A correct run looks roughly like:

```text
Loading facebook/esm2_t33_650M_UR50D ...
Model loaded. Parameters: 651,765,424
Running on: cuda

MB_fragment  (length 30)
HBB_fragment (length 31)

Embedding tensors:
  MB:  shape (30, 1280)
  HBB: shape (31, 1280)

Cross-similarity matrix:
  Shape: (30, 31)
  Mean similarity: 0.6213
  Max similarity:  0.9412
  Min similarity:  0.3147

Sequence-level cosine similarity (mean-pooled): 0.8472

Top-5 most-similar cross-protein residue pairs:
  MB[15]=W   HBB[15]=W   sim=0.9412
  MB[16]=G   HBB[16]=G   sim=0.9201
  MB[17]=K   HBB[17]=K   sim=0.8987
  MB[10]=L   HBB[14]=L   sim=0.8432
  MB[18]=V   HBB[18]=V   sim=0.8210
```

The numbers themselves vary, but the **conserved `WGK` motif**
typically dominates the top of the list. That's the model recognising,
without ever being told, the same motif you'd identify by hand from a
globin MSA.

## What you should learn

- **Embeddings are the contextualised representation of a residue.**
  They depend on the surrounding sequence, unlike the raw token
  embedding from module 9. A `W` in a globin has a different
  embedding from a `W` in an antibody.
- **Cosine similarity over embeddings ≈ "how alignable are these two
  positions?".** It's the continuous, contextual cousin of the BLOSUM62
  score from module 6.
- **Conserved motifs pop out automatically.** The `WGK` motif wasn't
  highlighted in the input; it emerges as the top of the similarity
  ranking.
- **Layer choice matters.** The final layer (33 in ESM-2 650M) is one
  reasonable choice, but middle layers (e.g. 30-32) sometimes give
  cleaner contact / similarity signal — see Rao et al, 2021. For this
  exercise we use the final layer.

## Memory and runtime

Two forward passes on 30-residue inputs take a few seconds on GPU,
maybe 30-60 seconds on CPU. Memory is dominated by the 2.6 GB model
weights; the embedding tensors themselves are tiny.
