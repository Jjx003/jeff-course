"""
Mask one residue in a short protein sequence and ask ESM-2 650M (via
HuggingFace transformers) to fill it in. See problem.md for the
expected output format. The probabilities themselves are not graded
(they depend on weights and version), but the overall structure of
the printed output is.
"""

from transformers.utils import logging as hf_logging

hf_logging.set_verbosity_error()

import torch
from transformers import AutoTokenizer, EsmForMaskedLM

CHECKPOINT = "facebook/esm2_t33_650M_UR50D"
SEQUENCE = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"
MASK_POS_1BASED = 14   # the W of the conserved WGK motif
AA_LETTERS = "ACDEFGHIKLMNPQRSTVWY"


def main() -> None:
    print(f"Loading {CHECKPOINT} ...")

    # TODO 1: Load the tokenizer and model from CHECKPOINT.
    # tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
    # model = EsmForMaskedLM.from_pretrained(CHECKPOINT)
    # model.eval()
    tokenizer = ...
    model = ...

    device = "cuda" if torch.cuda.is_available() else "cpu"
    # TODO 2: Move the model to `device`.

    # TODO 3: Print the parameter count and device:
    # n_params = sum(p.numel() for p in model.parameters())
    # print(f"Model loaded. Parameters: {n_params:,}")
    # print(f"Running on: {device}")

    print()
    print(f"Sequence (length {len(SEQUENCE)}):")
    print(SEQUENCE)
    print()

    original_residue = SEQUENCE[MASK_POS_1BASED - 1]

    # TODO 4: Build the tokenized input, then overwrite the mask position
    # in `input_ids` with `tokenizer.mask_token_id`.
    # The mask should land at token index MASK_POS_1BASED (because the
    # 1-based residue index equals the 0-based token index after <cls>).
    #
    #   inputs = tokenizer(SEQUENCE, return_tensors="pt").to(device)
    #   inputs["input_ids"][0, MASK_POS_1BASED] = tokenizer.mask_token_id
    #
    # For pretty printing, also build the masked-string form:
    masked_seq_str = SEQUENCE[: MASK_POS_1BASED - 1] + "<mask>" + SEQUENCE[MASK_POS_1BASED:]

    print(f"Masking position {MASK_POS_1BASED} (1-based, original residue '{original_residue}'):")
    print(masked_seq_str)
    print()

    # TODO 5: Forward pass under torch.inference_mode(). Pull out logits
    # for the mask token.
    #   with torch.inference_mode():
    #       out = model(**inputs)
    #   position_logits = out.logits[0, MASK_POS_1BASED]   # shape (V,)

    # TODO 6: Restrict to amino-acid tokens, softmax, take top-5.
    #   aa_token_ids = torch.tensor(
    #       [tokenizer.convert_tokens_to_ids(c) for c in AA_LETTERS],
    #       device=device,
    #   )
    #   aa_logits = position_logits[aa_token_ids]
    #   aa_probs  = torch.softmax(aa_logits, dim=-1)
    #   topk = torch.topk(aa_probs, k=5)

    # TODO 7: Print the top-5 block:
    #   "Top-5 predicted amino acids for the masked position:"
    #   "  X    p=0.NNNN"
    #   ...
    # then a blank line, then:
    #   "Top-1 matches original ('W'): True"


if __name__ == "__main__":
    main()
