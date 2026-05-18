"""
Reference solution for module 08.
"""

from io import StringIO

import numpy as np
from Bio.PDB import PDBParser

PDB_STRING = """\
HEADER    TOY HAIRPIN STRUCTURE
TITLE     SYNTHETIC 10-RESIDUE BETA-HAIRPIN-LIKE TRACE FOR MODULE 08
ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00 20.00           C
ATOM      2  CA  ALA A   2       3.800   0.000   0.000  1.00 20.00           C
ATOM      3  CA  ALA A   3       7.600   0.000   0.000  1.00 20.00           C
ATOM      4  CA  ALA A   4      11.400   0.000   0.000  1.00 20.00           C
ATOM      5  CA  ALA A   5      15.200   0.000   0.000  1.00 20.00           C
ATOM      6  CA  ALA A   6      15.200   3.800   0.000  1.00 20.00           C
ATOM      7  CA  ALA A   7      11.400   3.800   0.000  1.00 20.00           C
ATOM      8  CA  ALA A   8       7.600   3.800   0.000  1.00 20.00           C
ATOM      9  CA  ALA A   9       3.800   3.800   0.000  1.00 20.00           C
ATOM     10  CA  ALA A  10       0.000   3.800   0.000  1.00 20.00           C
TER      11      ALA A  10
END
"""


def main() -> None:
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("toy", StringIO(PDB_STRING))

    chain = structure[0]["A"]
    ca_atoms = [res["CA"] for res in chain
                if res.id[0] == " " and "CA" in res]

    n = len(ca_atoms)
    print(f"Parsed {n} alpha-carbons from chain A")

    first_three = [(res.get_resname(), res.id[1])
                   for res in list(chain)[:3]
                   if res.id[0] == " "]
    summary = ", ".join(f"{name}{num}" for name, num in first_three)
    print(f"First residues: {summary}")

    coords = np.array([atom.coord for atom in ca_atoms])
    diffs = coords[:, None, :] - coords[None, :, :]
    D = np.linalg.norm(diffs, axis=-1)

    print(f"Distance matrix shape: {D.shape}")

    eye_mask = ~np.eye(n, dtype=bool)
    min_nonzero = D[eye_mask].min()
    max_dist = D.max()
    print(f"Min non-zero distance: {min_nonzero:.3f} A")
    print(f"Max distance: {max_dist:.3f} A")

    idx = np.arange(n)
    sep = np.abs(idx[:, None] - idx[None, :])
    contact_mask = (D < 8.0) & (sep >= 2)
    n_contacts = int(np.triu(contact_mask).sum())
    print(f"Number of contacts (d < 8.0 A, |i-j| >= 2): {n_contacts}")


if __name__ == "__main__":
    main()
