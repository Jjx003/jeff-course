"""
Compute per-column Shannon entropy across a small globin-like MSA and
print the most-conserved positions. See problem.md for the exact
expected output format.
"""

import math
from collections import Counter
from io import StringIO

from Bio import AlignIO

MSA_FASTA = """\
>seq1
VLSPADKTNVKAAWGKVGAH
>seq2
VLSAEDKTNVKAAWAKVGAH
>seq3
VLSPGDKTNVKAEWGKVNAH
>seq4
VLSPADKTNVKAAWGKLGAH
>seq5
VLSPADKLDVKAAWGKVDAH
>seq6
ILSPADKTNVAAAWAKVGAH
"""


def main() -> None:
    # TODO 1: Parse the FASTA-formatted MSA.
    #         Hint: AlignIO.read(StringIO(MSA_FASTA), "fasta")
    align = ...

    n_seqs = ...
    n_cols = ...

    # TODO 2: Print the dimensions header
    # "MSA: {n_seqs} sequences x {n_cols} columns"

    # TODO 3: For each column, compute:
    #   - Shannon entropy in bits  H = -sum p log2 p over residues present
    #   - the most common residue and its count
    # Print one line per column in the format:
    #   "Col {i:>2}  H={H:.4f}  most_common={letter} ({count}/{n_seqs})"
    # Keep a list of (H, col_idx, letter, count) for the top-5 step.

    column_stats: list[tuple[float, int, str, int]] = []

    # TODO 4: Sort column_stats by (entropy, col_idx) ascending and print
    # the top 5 in the format:
    #   "Col {i:>2}  '{letter}' frequency {count}/{n_seqs}"


if __name__ == "__main__":
    main()
