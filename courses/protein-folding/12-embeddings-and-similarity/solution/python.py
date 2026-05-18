"""
Reference solution for module 12.
"""

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, EsmModel

MODEL_NAME = "facebook/esm2_t33_650M_UR50D"

MB  = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"
HBB = "VHLTPEEKSAVTALWGKVNVDEVGGEALGRL"


def main() -> None:
    print(f"Loading {MODEL_NAME} ...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = EsmModel.from_pretrained(MODEL_NAME)
    model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model loaded. Parameters: {n_params:,}")
    print(f"Running on: {device}")
    print()

    print(f"MB_fragment  (length {len(MB)})")
    print(f"HBB_fragment (length {len(HBB)})")
    print()

    @torch.inference_mode()
    def embed(seq: str) -> torch.Tensor:
        inputs = tokenizer(seq, return_tensors="pt").to(device)
        outputs = model(**inputs)
        # last_hidden_state has shape (1, L+2, 1280).
        # Strip <cls> at index 0 and <eos> at index L+1 to get (L, 1280).
        reps = outputs.last_hidden_state[0, 1 : 1 + len(seq)]
        return reps.cpu().float()

    mb_emb = embed(MB)
    hbb_emb = embed(HBB)

    print("Embedding tensors:")
    print(f"  MB:  shape {tuple(mb_emb.shape)}")
    print(f"  HBB: shape {tuple(hbb_emb.shape)}")
    print()

    mb_n = F.normalize(mb_emb, dim=-1)
    hbb_n = F.normalize(hbb_emb, dim=-1)
    sim = mb_n @ hbb_n.T

    print("Cross-similarity matrix:")
    print(f"  Shape: {tuple(sim.shape)}")
    print(f"  Mean similarity: {sim.mean().item():.4f}")
    print(f"  Max similarity:  {sim.max().item():.4f}")
    print(f"  Min similarity:  {sim.min().item():.4f}")
    print()

    # Per-sequence (mean-pooled) embedding: average over the residue dim
    # only, after stripping <cls> / <eos>. Then a single cosine number.
    mb_seq = F.normalize(mb_emb.mean(dim=0, keepdim=True), dim=-1)
    hbb_seq = F.normalize(hbb_emb.mean(dim=0, keepdim=True), dim=-1)
    seq_sim = F.cosine_similarity(mb_seq, hbb_seq).item()
    print(f"Sequence-level cosine similarity (mean-pooled): {seq_sim:.4f}")
    print()

    flat = sim.flatten()
    topk = torch.topk(flat, k=5)
    n_cols = sim.shape[1]
    print("Top-5 most-similar cross-protein residue pairs:")
    for s, idx in zip(topk.values.tolist(), topk.indices.tolist()):
        i, j = divmod(idx, n_cols)
        print(f"  MB[{i+1}]={MB[i]}   HBB[{j+1}]={HBB[j]}   sim={s:.4f}")


if __name__ == "__main__":
    main()
