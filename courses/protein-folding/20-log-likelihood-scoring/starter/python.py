"""
Score wild-type and mutant sequences with ESM-2 650M using the
pseudo-log-likelihood (PLL). Each position is masked one at a time;
the log-probability that the model assigns to the true residue is
summed across positions. This script needs ~6 GB of GPU VRAM at FP16.
The exact PLL values vary across hardware/versions, so the platform
does not grade exact numbers.
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
    # TODO 1: Tokenise the sequence (returns input_ids of shape [1, L+2]
    # with <cls> at index 0 and <eos> at index L+1). Move to device.

    # TODO 2: For each position i in 0..L-1:
    #   - Clone the token tensor.
    #   - Replace the token at index (i + 1) with tokenizer.mask_token_id.
    #   - Forward the masked tensor under torch.inference_mode().
    #   - F.log_softmax the float-cast logits at position (i + 1).
    #   - Read the log-prob at the true token id and add it to the sum.
    # Return the sum.
    return 0.0


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

    # TODO 3: Loop over each variant and compute its PLL.
    scores: dict[str, float] = {}

    print()
    wt_pll = scores.get("WT", 0.0)
    for name, _ in variants:
        p = scores.get(name, 0.0)
        if name == "WT":
            print(f"  {name:6s} PLL = {p:.3f}")
        else:
            print(f"  {name:6s} PLL = {p:.3f}   delta = {p - wt_pll:+7.3f}")

    print()
    print("Ranking (most likely first):")
    for rank, (name, _) in enumerate(sorted(variants, key=lambda v: -scores.get(v[0], 0.0)), start=1):
        print(f"  {rank}. {name:8s} PLL = {scores.get(name, 0.0):.3f}")


if __name__ == "__main__":
    main()
