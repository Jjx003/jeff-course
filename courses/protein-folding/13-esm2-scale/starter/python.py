"""
Sweep ESM-2 sizes (8M, 35M, 150M, 650M, 3B) on the masked-prediction
task from module 11. Print the size reference table, parameter counts,
forward-pass times, top-1 predictions, and end with a comparison table.
The 15B model is attempted separately at the end with try/except — it
won't fit on most desktop GPUs. See problem.md for the expected output.
"""

import time

import torch
from transformers import AutoTokenizer, EsmForMaskedLM

SEQUENCE = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"
MASK_POS_1BASED = 15  # the conserved W of the WGK motif (positions 15-17)
AA_LETTERS = "ACDEFGHIKLMNPQRSTVWY"

# (HuggingFace id, short name, params for table, embed dim, FP16 weights-only VRAM)
SIZE_TABLE = [
    ("facebook/esm2_t6_8M_UR50D",    "8M",   "8 M",   "320",  "~16 MB"),
    ("facebook/esm2_t12_35M_UR50D",  "35M",  "35 M",  "480",  "~70 MB"),
    ("facebook/esm2_t30_150M_UR50D", "150M", "150 M", "640",  "~300 MB"),
    ("facebook/esm2_t33_650M_UR50D", "650M", "650 M", "1280", "~1.3 GB"),
    ("facebook/esm2_t36_3B_UR50D",   "3B",   "3 B",   "2560", "~6 GB"),
    ("facebook/esm2_t48_15B_UR50D",  "15B",  "15 B",  "5120", "~30 GB"),
]

MODELS_TO_RUN = [row for row in SIZE_TABLE if row[1] != "15B"]
MODEL_15B = next(row for row in SIZE_TABLE if row[1] == "15B")


def print_size_table() -> None:
    # TODO 1: Print the size reference table from SIZE_TABLE in the
    # format shown in problem.md.
    pass


def build_masked_input() -> str:
    return (SEQUENCE[:MASK_POS_1BASED - 1]
            + "<mask>"
            + SEQUENCE[MASK_POS_1BASED:])


def time_forward(model, inputs, n_warmup: int = 1, n_runs: int = 3) -> float:
    # TODO 2: Run the model on `inputs` n_warmup + n_runs times under
    # torch.inference_mode(). Return the minimum elapsed time across the
    # n_runs timed runs. Use torch.cuda.synchronize() before/after each
    # run when on CUDA.
    return 0.0


def top1_for(hf_name: str, masked_seq: str, device: str):
    # TODO 3: Load tokenizer + EsmForMaskedLM by HuggingFace id, time a
    # forward pass, locate the <mask> token via tokenizer.mask_token_id,
    # extract the top-1 amino-acid prediction (over the 20 standard AAs),
    # and return (n_params, time_s, top1_letter, top1_prob). Don't
    # forget to free GPU memory (`del model; torch.cuda.empty_cache()`)
    # before returning so the next model fits.
    return 0, 0.0, "?", 0.0


def main() -> None:
    print_size_table()
    print()

    masked_seq = build_masked_input()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    results = []
    for hf_name, short, _params, _embed, _vram in MODELS_TO_RUN:
        print(f"Loading {hf_name} ...")
        try:
            n_params, t, letter, prob = top1_for(hf_name, masked_seq, device)
        except Exception as e:
            print(f"  Skipped {short}: {type(e).__name__}: {e}")
            print()
            if device == "cuda":
                torch.cuda.empty_cache()
            continue
        print(f"  Parameters: {n_params:,}")
        print(f"  Forward time (best of 3): {t:.4f} s")
        print(f"  Masked position {MASK_POS_1BASED} top-1: {letter}  p={prob:.4f}")
        print()
        results.append((short, letter, prob, t))

    # TODO 4: Print the comparison table at the end (size, top-1, p, time).

    # The 15B model rarely fits on a single desktop GPU. Wrap the load +
    # a 1-token forward pass in try/except so the script still finishes.
    print(f"Attempting to load {MODEL_15B[0]} (likely to fail) ...")
    try:
        tok_15b = AutoTokenizer.from_pretrained(MODEL_15B[0])
        model_15b = EsmForMaskedLM.from_pretrained(MODEL_15B[0])
        if device == "cuda":
            model_15b = model_15b.half().to(device)
        else:
            model_15b = model_15b.to(device)
        toks = tok_15b("M", return_tensors="pt").to(device)
        with torch.inference_mode():
            model_15b(**toks)
        print("  15B loaded and ran a 1-token forward pass — impressive hardware!")
    except Exception as e:
        print(f"  15B load failed: {type(e).__name__}")
        print("  This is expected on most desktop GPUs (15B needs ~30 GB VRAM).")


if __name__ == "__main__":
    main()
