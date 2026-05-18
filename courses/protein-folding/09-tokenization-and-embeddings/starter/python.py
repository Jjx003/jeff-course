"""
Tokenize a protein sequence with the HuggingFace ESM-2 8M tokenizer,
then look up the model's learned embedding for one residue. See
problem.md for the exact expected output format.
"""

from transformers.utils import logging as hf_logging

hf_logging.set_verbosity_error()

import torch
from transformers import AutoTokenizer, EsmModel

CHECKPOINT = "facebook/esm2_t6_8M_UR50D"
SEQUENCE = "MGLSDGEW"


def fmt_list(values) -> str:
    return "[" + ", ".join(f"{x:.4f}" for x in values) + "]"


def main() -> None:
    # TODO 1: Load the ESM-2 tokenizer with AutoTokenizer.from_pretrained(CHECKPOINT).
    tokenizer = ...

    # TODO 2: Print a header block. Use the tokenizer's *_token_id attributes
    # rather than hardcoded numbers:
    #   "ESM-2 tokenizer: facebook/esm2_t6_8M_UR50D"
    #   "  vocab_size: 33"
    #   "  <cls>=0  <pad>=1  <eos>=2  <unk>=3  <mask>=32"

    # TODO 3: Tokenize SEQUENCE. tokenizer(seq) returns a dict; the integer
    # IDs live at out["input_ids"]. By default <cls> and <eos> are included.
    # Then strip the <cls>/<eos> wrappers to get the per-residue IDs:
    #   aa_ids = ids[1:-1]
    ids = ...

    # TODO 4: Print the sequence block:
    #   "Sequence: MGLSDGEW (length 8)"
    #   "  Token IDs: [0, 20, 6, 4, 8, 13, 6, 9, 22, 2]"
    #   "  Encoded length (with <cls>/<eos>): 10"
    #   "  Distinct token IDs: 9"
    #   "  Per-residue IDs:"
    #   "    pos  1  M -> 20"   (use f"    pos {i:>2}  {aa} -> {tid}")
    #   ...

    # TODO 5: Load the model and put it in eval mode. We won't run a forward
    # pass — we just need its embedding matrix.
    #   model = EsmModel.from_pretrained(CHECKPOINT)
    #   model.eval()
    #   embedding_matrix = model.embeddings.word_embeddings.weight   # (33, 320)
    model = ...

    # TODO 6: Print the model block:
    #   "Loaded ESM-2 8M model"
    #   "  embedding matrix shape: (33, 320)"
    # Use tuple(embedding_matrix.shape) for the printed shape.

    # TODO 7: Look up the embedding for 'M' and print its stats:
    #   "Embedding for 'M' (token id 20)"
    #   "  shape: (320,)"
    #   "  first 4 values: [-0.1202, -0.0626, -0.0312, 0.0082]"
    #   "  last 4 values: [-0.4539, -0.2532, 0.0479, -0.0889]"
    #   "  sum of all 320 values: -4.5855"
    # Use the fmt_list helper above for the float lists, and 4 decimal
    # places for the sum.


if __name__ == "__main__":
    main()
