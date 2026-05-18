"""
Reference solution for module 18.

Loads ESMFold v1 via HuggingFace transformers and folds a short
peptide on the available GPU (FP16 backbone). Prints timing, parameter
count, mean / range pLDDT, and the first few PDB lines.
"""

import time
import torch
from transformers import EsmForProteinFolding

SEQUENCE = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"


def main() -> None:
    print("Loading ESMFold v1 ...")
    t0 = time.perf_counter()
    model = EsmForProteinFolding.from_pretrained(
        "facebook/esmfold_v1",
        low_cpu_mem_usage=True,
    )
    model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        model = model.cuda()
        # Half-precision the ESM-2 backbone only (structure module stays FP32
        # for numerical stability). This is the standard pattern from the
        # HuggingFace ESMFold docs and fits the 3B backbone in ~6-7 GB.
        model.esm = model.esm.half()
        torch.backends.cuda.matmul.allow_tf32 = True

        free_bytes = torch.cuda.mem_get_info()[0]
        if free_bytes < 12 * 1024 ** 3:
            print(f"  Free VRAM is {free_bytes / 1024 ** 3:.1f} GB; using chunk_size=64")
            model.trunk.set_chunk_size(64)

    load_time = time.perf_counter() - t0
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model loaded in {load_time:.2f} s")
    print(f"Parameters: {n_params:,}")
    print()

    print(f"Sequence (length {len(SEQUENCE)}):")
    print(SEQUENCE)
    print()

    print(f"Folding (FP16 on {device}) ...")
    t0 = time.perf_counter()
    with torch.no_grad():
        pdb_str = model.infer_pdb(SEQUENCE)
    if device == "cuda":
        torch.cuda.synchronize()
    fold_time = time.perf_counter() - t0
    print(f"Forward pass: {fold_time:.2f} s")
    print()

    plddts: list[float] = []
    seen: set[int] = set()
    for line in pdb_str.splitlines():
        if line.startswith("ATOM"):
            try:
                plddt = float(line[60:66].strip())
                resi = int(line[22:26].strip())
            except ValueError:
                continue
            if resi not in seen:
                plddts.append(plddt)
                seen.add(resi)

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
