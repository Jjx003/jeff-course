## Hints

1. Loading + tokenising both sequences (HuggingFace `transformers`):

```python
import torch
from transformers import AutoTokenizer, EsmModel

MODEL_NAME = "facebook/esm2_t33_650M_UR50D"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = EsmModel.from_pretrained(MODEL_NAME)
model.eval()
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

MB  = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"
HBB = "VHLTPEEKSAVTALWGKVNVDEVGGEALGRL"

@torch.inference_mode()
def embed(seq: str) -> torch.Tensor:
    inputs = tokenizer(seq, return_tensors="pt").to(device)
    out = model(**inputs)
    reps = out.last_hidden_state[0]      # (L+2, 1280)
    return reps[1 : 1 + len(seq)].cpu()  # strip <cls> + <eos>
```

We use `EsmModel` (no LM head) rather than `EsmForMaskedLM` because we
only want hidden states. `model(**inputs)` returns a
`BaseModelOutputWithPooling`; its `.last_hidden_state` is the
`(batch, L+2, 1280)` tensor we want.

2. L2-normalise per row (per residue) so dot products give cosines:

```python
import torch.nn.functional as F
mb_emb  = F.normalize(embed(MB),  dim=-1)
hbb_emb = F.normalize(embed(HBB), dim=-1)
```

3. The full cross-similarity matrix is one matmul:

```python
sim = mb_emb @ hbb_emb.T            # (30, 31)
```

4. Mean-pool for a single sequence-level cosine:

```python
mb_seq  = F.normalize(embed(MB).mean(dim=0,  keepdim=True), dim=-1)
hbb_seq = F.normalize(embed(HBB).mean(dim=0, keepdim=True), dim=-1)
seq_sim = F.cosine_similarity(mb_seq, hbb_seq).item()
```

Critical: pool **after** stripping `<cls>` / `<eos>`. Including them
shifts every per-sequence vector toward the average `<cls>` / `<eos>`
direction and pulls all sequence-level similarities toward 1.

5. Top-5 by flatten + topk:

```python
flat = sim.flatten()                # (30 * 31,)
topk = torch.topk(flat, k=5)
for s, idx in zip(topk.values.tolist(), topk.indices.tolist()):
    i, j = divmod(idx, sim.shape[1])
    print(f"  MB[{i+1}]={MB[i]}   HBB[{j+1}]={HBB[j]}   sim={s:.4f}")
```

The `divmod(idx, sim.shape[1])` trick converts a flat index back into
`(row, col)` coordinates.

## CPU fallback

Same advice as module 11. Drop the `.cuda()` calls and expect ~30-60
seconds per forward pass on a typical laptop. The pairwise similarity
computation is millisecond-fast either way.

## Sanity checks

- `mb_emb.shape == (30, 1280)`, `hbb_emb.shape == (31, 1280)`. If
  you have `(32, 1280)` for MB you forgot to strip `<cls>`/`<eos>`.
- Diagonal-ish patterns in the similarity matrix are normal: `sim[i, i]`
  for similar globin sequences tends to be on the high end because
  same-position residues in evolutionarily related proteins are most
  similar.
- The single highest similarity is almost always at the conserved
  `WGK` motif. If you don't see `W`-`W` near the top, double-check
  your indexing (especially the `<cls>` strip).
- After normalisation, every row of `mb_emb` should have L2 norm 1.
  Confirm with `mb_emb.norm(dim=-1)`.

## Going deeper

- **Rao et al, 2021** — *MSA Transformer* — [https://www.biorxiv.org/content/10.1101/2021.02.12.430858](https://www.biorxiv.org/content/10.1101/2021.02.12.430858). Shows that PLMs trained directly on MSAs produce per-residue embeddings that recover MSA-level structural signal explicitly.
- **Rives et al, 2019** — *Biological structure and function emerge from scaling unsupervised learning to 250 million protein sequences* — [https://www.biorxiv.org/content/10.1101/622803](https://www.biorxiv.org/content/10.1101/622803). The paper that first demonstrated PLM embeddings encode secondary structure, contacts, and function.
- **HuggingFace ESM docs** — [https://huggingface.co/docs/transformers/model_doc/esm](https://huggingface.co/docs/transformers/model_doc/esm). The `EsmModel` / `EsmForMaskedLM` API used in this module, plus the full list of `facebook/esm2_*` checkpoints on the Hub.
- **`fair-esm` representations example** — [https://github.com/facebookresearch/esm/blob/main/scripts/extract.py](https://github.com/facebookresearch/esm/blob/main/scripts/extract.py). The original embedding-extraction script from the Meta release; useful when you need richer per-layer outputs than the HuggingFace wrapper exposes.
- **Brandes et al, 2022** — *ProteinBERT: a universal deep-learning model of protein sequence and function* — [https://academic.oup.com/bioinformatics/article/38/8/2102/6515282](https://academic.oup.com/bioinformatics/article/38/8/2102/6515282). An alternative PLM with explicit functional annotation pretraining tasks.

## Things to try after

1. **Plot the similarity matrix.** `plt.imshow(sim.cpu(), cmap='viridis')`
   gives you a 30 × 31 heatmap. The conserved motifs show up as a
   bright cross.
2. **Compare layers.** Re-run with `output_hidden_states=True` and pull
   `out.hidden_states[10]`, `out.hidden_states[20]`, `out.hidden_states[33]`.
   Compute the cosine similarity at each layer. The early-layer
   similarity is dominated by amino-acid identity; later layers
   capture structural / contextual features.
3. **Try unrelated proteins.** Replace HBB_fragment with a kinase or
   antibody fragment. The mean similarity should drop sharply, and
   the top-5 list should be far less coherent.
4. **Whole-sequence similarity.** Mean-pool the per-residue embeddings
   to get a single 1280-dim vector per protein, then compute a single
   cosine similarity number. This is the standard "how related are
   these two proteins?" PLM embedding score.

Next module: ESM-2 at scale — load multiple model sizes and watch
prediction quality improve with parameters.
