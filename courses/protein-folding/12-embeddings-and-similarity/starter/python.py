"""
Extract per-residue embeddings from ESM-2 650M for two globin fragments
and compute the pairwise cosine-similarity matrix. Output structure is
described in problem.md; the exact numerical values depend on weights
and version, so they are not graded.
"""

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, EsmModel

MODEL_NAME = "facebook/esm2_t33_650M_UR50D"

MB  = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"
HBB = "VHLTPEEKSAVTALWGKVNVDEVGGEALGRL"


def main() -> None:
    print(f"Loading {MODEL_NAME} ...")
    # TODO 1: Load tokenizer + model via HuggingFace transformers, set
    # the model to eval mode, and move it to device.
    # tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    # model = EsmModel.from_pretrained(MODEL_NAME)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    # n_params = sum(p.numel() for p in model.parameters())
    # print(f"Model loaded. Parameters: {n_params:,}")
    # print(f"Running on: {device}")
    print()

    print(f"MB_fragment  (length {len(MB)})")
    print(f"HBB_fragment (length {len(HBB)})")
    print()

    # TODO 2: Define a helper that tokenises one sequence, runs the model
    # under torch.inference_mode(), and returns the (L, 1280) per-residue
    # representation (strip <cls> at index 0 and <eos> at index L+1).

    def embed(seq: str) -> torch.Tensor:
        ...

    mb_emb = embed(MB)
    hbb_emb = embed(HBB)

    print("Embedding tensors:")
    print(f"  MB:  shape {tuple(mb_emb.shape)}")
    print(f"  HBB: shape {tuple(hbb_emb.shape)}")
    print()

    # TODO 3: L2-normalise both, compute the (30, 31) cross-similarity
    # matrix, and print mean / max / min.
    mb_n  = F.normalize(mb_emb,  dim=-1)
    hbb_n = F.normalize(hbb_emb, dim=-1)
    sim = mb_n @ hbb_n.T
    print("Cross-similarity matrix:")
    print(f"  Shape: {tuple(sim.shape)}")
    print(f"  Mean similarity: {sim.mean().item():.4f}")
    print(f"  Max similarity:  {sim.max().item():.4f}")
    print(f"  Min similarity:  {sim.min().item():.4f}")
    print()

    # TODO 4: Also compute a single sequence-level cosine similarity by
    # mean-pooling each (L, 1280) tensor over the residue dim (only) and
    # then calling F.cosine_similarity on the two resulting vectors.

    # TODO 5: Find the top-5 entries of `sim` and print one per line:
    #   "  MB[i+1]=A   HBB[j+1]=A   sim=0.NNNN"
    # Hint: torch.topk on flatten, then divmod to recover (i, j).


if __name__ == "__main__":
    main()
