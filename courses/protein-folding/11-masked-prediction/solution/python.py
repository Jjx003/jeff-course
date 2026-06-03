"""
Reference solution for module 11.
"""

from transformers.utils import logging as hf_logging

hf_logging.set_verbosity_error()

import torch
from transformers import AutoTokenizer, EsmForMaskedLM

CHECKPOINT = "facebook/esm2_t33_650M_UR50D"
SEQUENCE = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"
MASK_POS_1BASED = 15  # the W of the conserved WGK motif (positions 15-17)
AA_LETTERS = "ACDEFGHIKLMNPQRSTVWY"


def main() -> None:
    print(f"Loading {CHECKPOINT} ...")
    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
    model = EsmForMaskedLM.from_pretrained(CHECKPOINT)
    model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model loaded. Parameters: {n_params:,}")
    print(f"Running on: {device}")
    print()

    print(f"Sequence (length {len(SEQUENCE)}):")
    print(SEQUENCE)
    print()

    original_residue = SEQUENCE[MASK_POS_1BASED - 1]

    inputs = tokenizer(SEQUENCE, return_tensors="pt").to(device)
    inputs["input_ids"][0, MASK_POS_1BASED] = tokenizer.mask_token_id

    assert inputs["input_ids"][0, MASK_POS_1BASED].item() == tokenizer.mask_token_id, (
        "Mask token did not land at the expected position"
    )

    masked_seq_str = (
        SEQUENCE[: MASK_POS_1BASED - 1] + "<mask>" + SEQUENCE[MASK_POS_1BASED:]
    )
    print(f"Masking position {MASK_POS_1BASED} (1-based, original residue '{original_residue}'):")
    print(masked_seq_str)
    print()

    with torch.inference_mode():
        out = model(**inputs)
    position_logits = out.logits[0, MASK_POS_1BASED]

    aa_token_ids = torch.tensor(
        [tokenizer.convert_tokens_to_ids(c) for c in AA_LETTERS],
        device=device,
    )
    aa_logits = position_logits[aa_token_ids]
    aa_probs = torch.softmax(aa_logits, dim=-1)
    topk = torch.topk(aa_probs, k=5)

    print("Top-5 predicted amino acids for the masked position:")
    for prob, idx in zip(topk.values.tolist(), topk.indices.tolist()):
        letter = AA_LETTERS[idx]
        print(f"  {letter}    p={prob:.4f}")
    print()

    top1_letter = AA_LETTERS[topk.indices[0].item()]
    matches = top1_letter == original_residue
    print(f"Top-1 matches original ('{original_residue}'): {matches}")


if __name__ == "__main__":
    main()
