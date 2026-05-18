"""
Parse a small embedded PDB structure with Biopython, extract alpha-carbon
coordinates from chain A, and compute distance / contact statistics.
See problem.md for the exact expected output format.
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
    # TODO 1: Parse the PDB string with PDBParser. Use QUIET=True to silence
    # warnings. Hint: parser.get_structure("toy", StringIO(PDB_STRING)).
    structure = ...

    # TODO 2: Walk into chain A, collect a list of CA atoms from standard
    # residues only (skip HETATM with res.id[0] == " " and "CA" in res).
    ca_atoms = ...

    # TODO 3: Print the count and the first three residues' (resname, resseq).
    # Format: "Parsed N alpha-carbons from chain A"
    #         "First residues: <name><num>, <name><num>, <name><num>"

    # TODO 4: Stack atom.coord into an (N, 3) numpy array, compute the
    # pairwise distance matrix D of shape (N, N).
    coords = ...
    D = ...

    # TODO 5: Compute and print:
    #   - the matrix shape (use D.shape)
    #   - the min non-zero distance (mask out the diagonal)
    #   - the max distance
    #   - the number of contacts (D < 8.0 AND |i-j| >= 2), counted on the
    #     upper or lower triangle to avoid double-counting.


if __name__ == "__main__":
    main()
