"""
Reference solution for module 13.
"""

import time

import torch
from transformers import AutoTokenizer, EsmForMaskedLM

SEQUENCE = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"
MASK_POS_1BASED = 14
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

# Run end-to-end masked-prediction across these sizes. 15B is handled
# separately at the bottom with a try/except (won't fit on most GPUs).
MODELS_TO_RUN = [row for row in SIZE_TABLE if row[1] != "15B"]
MODEL_15B = next(row for row in SIZE_TABLE if row[1] == "15B")


def print_size_table() -> None:
    print("ESM-2 model size reference")
    print(f"  {'Name':<34} {'Params':>8}   {'Embed dim':<10}  VRAM (FP16, weights only)")
    for hf_name, _short, params, embed, vram in SIZE_TABLE:
        print(f"  {hf_name:<34} {params:>8}   {embed:<10}  {vram}")


def build_masked_input() -> str:
    return (SEQUENCE[:MASK_POS_1BASED - 1]
            + "<mask>"
            + SEQUENCE[MASK_POS_1BASED:])


def time_forward(model, inputs, n_warmup: int = 1, n_runs: int = 3) -> float:
    use_cuda = inputs.input_ids.is_cuda
    for _ in range(n_warmup):
        with torch.inference_mode():
            model(**inputs)
        if use_cuda:
            torch.cuda.synchronize()
    times = []
    for _ in range(n_runs):
        if use_cuda:
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.inference_mode():
            model(**inputs)
        if use_cuda:
            torch.cuda.synchronize()
        times.append(time.perf_counter() - t0)
    return min(times)


def top1_for(hf_name: str, masked_seq: str, device: str):
    tokenizer = AutoTokenizer.from_pretrained(hf_name)
    model = EsmForMaskedLM.from_pretrained(hf_name)
    model.eval()
    if device == "cuda":
        model = model.half().to(device)
    else:
        model = model.to(device)

    n_params = sum(p.numel() for p in model.parameters())

    inputs = tokenizer(masked_seq, return_tensors="pt").to(device)
    mask_index = int(
        (inputs.input_ids[0] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0].item()
    )

    t = time_forward(model, inputs)

    with torch.inference_mode():
        out = model(**inputs)
    logits = out.logits[0, mask_index]

    aa_ids = torch.tensor(
        [tokenizer.convert_tokens_to_ids(c) for c in AA_LETTERS], device=device
    )
    # Cast to float32 before softmax: FP16 softmax can underflow.
    aa_probs = torch.softmax(logits[aa_ids].float(), dim=-1)
    top1_idx = int(aa_probs.argmax().item())
    top1_letter = AA_LETTERS[top1_idx]
    top1_prob = float(aa_probs[top1_idx].item())

    del model, tokenizer
    if device == "cuda":
        torch.cuda.empty_cache()

    return n_params, t, top1_letter, top1_prob


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
            # The 3B model can OOM on smaller cards (~24 GB or less);
            # any other RuntimeError / OSError is also caught here so the
            # script still reaches the comparison table at the end.
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

    print("Comparison")
    print(f"  {'Size':<8} {'Top-1':<7} {'p(top-1)':<10} {'Forward (s)':<12}")
    for short, letter, prob, t in results:
        print(f"  {short:<8} {letter:<7} {prob:<10.4f} {t:<12.4f}")

    print()
    print(f"Attempting to load {MODEL_15B[0]} (likely to fail) ...")
    # The 15B checkpoint is ~30 GB in FP16 alone; an 80 GB A100 / H100 can
    # fit it, almost nothing else can. We do a single 1-token forward
    # pass to demonstrate the API and rely on try/except for the
    # expected OOM / download failure on smaller hardware.
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
        del model_15b, tok_15b
        if device == "cuda":
            torch.cuda.empty_cache()
    except Exception as e:
        print(f"  15B load failed: {type(e).__name__}")
        print("  This is expected on most desktop GPUs (15B needs ~30 GB VRAM).")


if __name__ == "__main__":
    main()
