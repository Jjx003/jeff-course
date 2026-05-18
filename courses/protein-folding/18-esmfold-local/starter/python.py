"""
Fold a short peptide with ESMFold v1 and inspect the predicted PDB.
This module needs ~10-16 GB of GPU VRAM to run smoothly. CPU is
discouraged (it works but takes 10+ minutes). The output structure
itself is non-deterministic in the small details, so the platform
does not grade exact values.

Uses the HuggingFace transformers port of ESMFold
(`facebook/esmfold_v1`) which is the most reliable way to run it
locally — no openfold / fair-esm install pain.
"""

import time
import torch
from transformers import EsmForProteinFolding

SEQUENCE = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"


def main() -> None:
    print("Loading ESMFold v1 ...")
    t0 = time.perf_counter()

    # TODO 1: Load the model with EsmForProteinFolding.from_pretrained(
    #     "facebook/esmfold_v1", low_cpu_mem_usage=True
    # ), set eval mode, and move to cuda if available.
    # model = ...
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # TODO 2: For GPU runs, half-precision the ESM-2 backbone with
    # `model.esm = model.esm.half()` to fit a 16 GB card. Optionally
    # call model.trunk.set_chunk_size(64) when free VRAM is tight.

    load_time = time.perf_counter() - t0
    # n_params = sum(p.numel() for p in model.parameters())
    # print(f"Model loaded in {load_time:.2f} s")
    # print(f"Parameters: {n_params:,}")
    print()

    print(f"Sequence (length {len(SEQUENCE)}):")
    print(SEQUENCE)
    print()

    print(f"Folding (FP16 on {device}) ...")

    # TODO 3: Run the forward pass under no_grad. Use model.infer_pdb to
    # get the PDB string directly (it handles tokenisation and trims the
    # cls / eos tokens internally).
    t0 = time.perf_counter()
    pdb_str = "...REPLACE..."
    if device == "cuda":
        torch.cuda.synchronize()
    fold_time = time.perf_counter() - t0
    print(f"Forward pass: {fold_time:.2f} s")
    print()

    # TODO 4: Parse the B-factor column (pLDDT) per residue from pdb_str.
    plddts: list[float] = []

    print("Result:")
    print(f"  Sequence length: {len(SEQUENCE)}")
    if plddts:
        mean_plddt = sum(plddts) / len(plddts)
        print(f"  Mean pLDDT:      {mean_plddt:.1f}")
        print(f"  pLDDT range:     [{min(plddts):.1f}, {max(plddts):.1f}]")
    print()

    print("First 8 lines of predicted PDB:")
    for line in pdb_str.splitlines()[:8]:
        print(line)


if __name__ == "__main__":
    main()
