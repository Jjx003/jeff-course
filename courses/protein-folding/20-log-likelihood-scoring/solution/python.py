"""
Reference solution for module 20.
"""

from transformers.utils import logging as hf_logging

hf_logging.set_verbosity_error()

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, EsmForMaskedLM

CHECKPOINT = "facebook/esm2_t33_650M_UR50D"
WILD_TYPE = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"

MUTATIONS = [
    ("W8A", 8, "A"),
    ("W15A", 15, "A"),
    ("K17R", 17, "R"),
    ("A20V", 20, "V"),
]


def apply_mutation(seq: str, position_1based: int, new_aa: str) -> str:
    return seq[:position_1based - 1] + new_aa + seq[position_1based:]


def pll(model, tokenizer, sequence: str, device: str) -> float:
    mask_id = tokenizer.mask_token_id
    inputs = tokenizer(sequence, return_tensors="pt").to(device)
    token_ids = inputs["input_ids"]
    L = len(sequence)
    log_prob_sum = 0.0
    for i in range(L):
        masked = token_ids.clone()
        masked[0, i + 1] = mask_id
        with torch.inference_mode():
            logits = model(input_ids=masked).logits
        log_probs = F.log_softmax(logits[0, i + 1].float(), dim=-1)
        true_token_id = token_ids[0, i + 1].item()
        log_prob_sum += float(log_probs[true_token_id].item())
    return log_prob_sum


def main() -> None:
    print(f"Loading {CHECKPOINT} ...")
    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
    model = EsmForMaskedLM.from_pretrained(CHECKPOINT)
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.half().to(device) if device == "cuda" else model.to(device)

    print()
    print("ESM-2 650M pseudo-log-likelihood scoring")
    print(f"Wild-type sequence (length {len(WILD_TYPE)}):")
    print(WILD_TYPE)
    print()

    variants = [("WT", WILD_TYPE)]
    for name, pos, new_aa in MUTATIONS:
        variants.append((name, apply_mutation(WILD_TYPE, pos, new_aa)))

    n_passes = len(variants) * len(WILD_TYPE)
    print(f"Computing PLL for {len(variants)} sequences x {len(WILD_TYPE)} positions = {n_passes} forward passes ...")

    scores: dict[str, float] = {}
    for name, seq in variants:
        scores[name] = pll(model, tokenizer, seq, device)

    wt_pll = scores["WT"]
    print()
    for name, _ in variants:
        p = scores[name]
        if name == "WT":
            print(f"  {name:6s} PLL = {p:.3f}")
        else:
            print(f"  {name:6s} PLL = {p:.3f}   delta = {p - wt_pll:+7.3f}")

    print()
    print("Ranking (most likely first):")
    for rank, (name, _) in enumerate(sorted(variants, key=lambda v: -scores[v[0]]), start=1):
        print(f"  {rank}. {name:8s} PLL = {scores[name]:.3f}")


if __name__ == "__main__":
    main()
