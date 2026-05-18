"""
Reference solution for module 09.
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
    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)

    print(f"ESM-2 tokenizer: {CHECKPOINT}")
    print(f"  vocab_size: {tokenizer.vocab_size}")
    specials = (
        f"<cls>={tokenizer.cls_token_id}  "
        f"<pad>={tokenizer.pad_token_id}  "
        f"<eos>={tokenizer.eos_token_id}  "
        f"<unk>={tokenizer.unk_token_id}  "
        f"<mask>={tokenizer.mask_token_id}"
    )
    print(f"  {specials}")
    print()

    ids = tokenizer(SEQUENCE)["input_ids"]
    aa_ids = ids[1:-1]

    print(f"Sequence: {SEQUENCE} (length {len(SEQUENCE)})")
    print(f"  Token IDs: {ids}")
    print(f"  Encoded length (with <cls>/<eos>): {len(ids)}")
    print(f"  Distinct token IDs: {len(set(ids))}")
    print("  Per-residue IDs:")
    for i, (aa, tid) in enumerate(zip(SEQUENCE, aa_ids), start=1):
        print(f"    pos {i:>2}  {aa} -> {tid}")
    print()

    model = EsmModel.from_pretrained(CHECKPOINT)
    model.eval()

    embedding_matrix = model.embeddings.word_embeddings.weight
    print("Loaded ESM-2 8M model")
    print(f"  embedding matrix shape: {tuple(embedding_matrix.shape)}")
    print()

    m_id = tokenizer.convert_tokens_to_ids("M")
    with torch.no_grad():
        m_vec = embedding_matrix[m_id].detach()

    print(f"Embedding for 'M' (token id {m_id})")
    print(f"  shape: {tuple(m_vec.shape)}")
    print(f"  first 4 values: {fmt_list(m_vec[:4].tolist())}")
    print(f"  last 4 values: {fmt_list(m_vec[-4:].tolist())}")
    print(f"  sum of all {m_vec.shape[0]} values: {float(m_vec.sum()):.4f}")


if __name__ == "__main__":
    main()
