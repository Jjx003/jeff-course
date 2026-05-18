"""
Reference solution for module 06.
"""

from Bio import Align
from Bio.Align import substitution_matrices

MB_FRAGMENT = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"
HBB_FRAGMENT = "VHLTPEEKSAVTALWGKVNVDEVGGEALGRL"


def main() -> None:
    aligner = Align.PairwiseAligner()
    aligner.mode = "global"
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    # PairwiseAligner's gap-score defaults are 0 (free gaps), which produces
    # nonsense alignments. -10 / -1 is the canonical BLAST-style choice for
    # BLOSUM62 and yields a single optimal alignment for this pair.
    aligner.open_gap_score = -10
    aligner.extend_gap_score = -1

    alignments = aligner.align(MB_FRAGMENT, HBB_FRAGMENT)
    best = alignments[0]

    aligned_a = str(best[0])
    aligned_b = str(best[1])
    aln_length = len(aligned_a)
    non_gap_columns = sum(1 for a, b in zip(aligned_a, aligned_b)
                          if a != "-" and b != "-")
    matches = sum(1 for a, b in zip(aligned_a, aligned_b)
                  if a == b and a != "-")

    print("Aligning MB_fragment vs HBB_fragment")
    print("Substitution matrix: BLOSUM62")
    print("Mode: global")
    print()
    print("Alignment:")
    print(str(best), end="")
    print(f"Score: {best.score:.1f}")
    print(f"Identity: {matches}/{non_gap_columns} "
          f"({100 * matches / non_gap_columns:.1f}%)")
    print(f"Alignment length: {aln_length}")


if __name__ == "__main__":
    main()
