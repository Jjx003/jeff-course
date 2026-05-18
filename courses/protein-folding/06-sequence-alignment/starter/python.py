"""
Pairwise global alignment of two protein fragments using BLOSUM62.
See problem.md for the exact expected output format.
"""

from Bio import Align
from Bio.Align import substitution_matrices

MB_FRAGMENT = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"
HBB_FRAGMENT = "VHLTPEEKSAVTALWGKVNVDEVGGEALGRL"


def main() -> None:
    # TODO 1: Create a PairwiseAligner in 'global' mode, load BLOSUM62, and
    #         set realistic affine gap scores (open=-10, extend=-1).
    #         The Biopython defaults of 0 give free gaps and produce nonsense
    #         alignments; -10 / -1 is the canonical BLAST-style choice.
    aligner = ...

    # TODO 2: Compute alignments between MB_FRAGMENT and HBB_FRAGMENT,
    #         and grab the top-scoring one.
    best = ...

    # TODO 3: Compute identity. Walk the two aligned strings (best[0],
    #         best[1]) and count positions where they are equal AND
    #         neither side is a gap '-'. The denominator for the printed
    #         percentage is the number of non-gap columns (positions
    #         where neither side has '-').
    matches = ...
    non_gap_columns = ...
    aln_length = ...

    # TODO 4: Print the required output. See problem.md for the exact
    # header lines, then print(best) for the alignment block, then the
    # Score / Identity / Alignment length lines.

    print("Aligning MB_fragment vs HBB_fragment")
    print("Substitution matrix: BLOSUM62")
    print("Mode: global")
    print()
    print("Alignment:")
    # print(best) here
    # then the numeric summary lines


if __name__ == "__main__":
    main()
