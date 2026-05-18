"""
Reference solution for module 19.
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
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("s", StringIO(pdb_str))
    ca = [res["CA"] for res in structure[0]["A"]
          if res.id[0] == " " and "CA" in res]
    return np.array([atom.coord for atom in ca])


def rmsd_and_distances(p: np.ndarray, q: np.ndarray) -> tuple[float, np.ndarray]:
    diffs = p - q
    distances = np.linalg.norm(diffs, axis=1)
    rms = float(np.sqrt(np.mean(distances ** 2)))
    return rms, distances


def tm_like(distances: np.ndarray, d0: float) -> float:
    return float(np.mean(1.0 / (1.0 + (distances / d0) ** 2)))


def plddt_per_residue(pdb_str: str) -> list[float]:
    plddts: list[float] = []
    seen: set[int] = set()
    for line in pdb_str.splitlines():
        if not line.startswith("ATOM"):
            continue
        try:
            bfac = float(line[60:66].strip())
            resi = int(line[22:26].strip())
        except ValueError:
            continue
        if resi not in seen:
            plddts.append(bfac)
            seen.add(resi)
    return plddts


def main() -> None:
    p_true = ca_coords(PDB_TRUE)
    p_pred = ca_coords(PDB_PRED)

    rms, distances = rmsd_and_distances(p_pred, p_true)
    print("RMSD computation")
    print(f"  Atoms compared: {len(p_true)}")
    dist_str = "[" + ", ".join(f"{x:.3f}" for x in distances) + "]"
    print(f"  Per-residue distances (A): {dist_str}")
    print(f"  RMSD: {rms:.4f} A")
    print()

    score = tm_like(distances, D0)
    print(f"TM-score-like metric (d_0 = {D0:.3f})")
    print(f"  Score: {score:.4f}")
    print()

    plddts = plddt_per_residue(PDB_PLDDT)
    n = len(plddts)
    print("pLDDT analysis")
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
