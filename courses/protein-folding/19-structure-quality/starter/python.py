"""
Compute structural quality metrics on toy embedded PDBs:
RMSD, TM-score-like, and pLDDT distribution analysis. See problem.md
for the exact expected output format.
"""

from io import StringIO

import numpy as np
from Bio.PDB import PDBParser

PDB_TRUE = """\
ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00  0.00           C
ATOM      2  CA  ALA A   2       3.800   0.000   0.000  1.00  0.00           C
ATOM      3  CA  ALA A   3       7.600   0.000   0.000  1.00  0.00           C
ATOM      4  CA  ALA A   4      11.400   0.000   0.000  1.00  0.00           C
ATOM      5  CA  ALA A   5      15.200   0.000   0.000  1.00  0.00           C
TER
END
"""

PDB_PRED = """\
ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00  0.00           C
ATOM      2  CA  ALA A   2       3.800   0.000   0.000  1.00  0.00           C
ATOM      3  CA  ALA A   3       7.600   0.000   1.000  1.00  0.00           C
ATOM      4  CA  ALA A   4      11.400   0.000  -1.000  1.00  0.00           C
ATOM      5  CA  ALA A   5      15.200   0.000   0.000  1.00  0.00           C
TER
END
"""

PDB_PLDDT = """\
ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00 88.00           C
ATOM      2  CA  ALA A   2       3.800   0.000   0.000  1.00 75.00           C
ATOM      3  CA  ALA A   3       7.600   0.000   0.000  1.00 62.00           C
ATOM      4  CA  ALA A   4      11.400   0.000   0.000  1.00 92.00           C
ATOM      5  CA  ALA A   5      15.200   0.000   0.000  1.00 81.00           C
TER
END
"""

D0 = 2.0


def ca_coords(pdb_str: str) -> np.ndarray:
    # TODO 1: Parse with PDBParser, return (N, 3) numpy array of CA coords.
    return np.zeros((0, 3))


def rmsd_and_distances(p: np.ndarray, q: np.ndarray) -> tuple[float, np.ndarray]:
    # TODO 2: Compute the per-pair Euclidean distance and the RMSD.
    return 0.0, np.zeros(0)


def tm_like(distances: np.ndarray, d0: float) -> float:
    # TODO 3: Compute (1/L) * sum_i 1 / (1 + (d_i / d0)^2).
    return 0.0


def plddt_per_residue(pdb_str: str) -> list[float]:
    # TODO 4: Walk ATOM lines and extract one B-factor per unique residue.
    return []


def main() -> None:
    p_true = ca_coords(PDB_TRUE)
    p_pred = ca_coords(PDB_PRED)

    rms, distances = rmsd_and_distances(p_pred, p_true)
    print("RMSD computation")
    print(f"  Atoms compared: {len(p_true)}")
    print(f"  Per-residue distances (A): [" + ", ".join(f"{x:.3f}" for x in distances) + "]")
    print(f"  RMSD: {rms:.4f} A")
    print()

    score = tm_like(distances, D0)
    print(f"TM-score-like metric (d_0 = {D0:.3f})")
    print(f"  Score: {score:.4f}")
    print()

    plddts = plddt_per_residue(PDB_PLDDT)
    n = len(plddts)
    print("pLDDT analysis")
    if n == 0:
        print("  (no residues parsed)")
        return
    arr = np.array(plddts)
    n_above_70 = int((arr > 70).sum())
    n_above_90 = int((arr > 90).sum())
    print(f"  Residues: {n}")
    print(f"  Mean pLDDT: {arr.mean():.2f}")
    print(f"  Min pLDDT:  {arr.min():.2f}")
    print(f"  Max pLDDT:  {arr.max():.2f}")
    print(f"  Fraction with pLDDT > 70: {n_above_70/n:.2f} ({n_above_70}/{n})")
    print(f"  Fraction with pLDDT > 90: {n_above_90/n:.2f} ({n_above_90}/{n})")


if __name__ == "__main__":
    main()
