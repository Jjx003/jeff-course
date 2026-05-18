"""
Reference solution for module 07.
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


def shannon_entropy_bits(counts: Counter, n: int) -> float:
    H = 0.0
    for count in counts.values():
        if count == 0:
            continue
        p = count / n
        H -= p * math.log2(p)
    return H


def main() -> None:
    align = AlignIO.read(StringIO(MSA_FASTA), "fasta")
    n_seqs = len(align)
    n_cols = align.get_alignment_length()

    print(f"MSA: {n_seqs} sequences x {n_cols} columns")
    print()
    print("Per-column Shannon entropy (bits):")

    column_stats: list[tuple[float, int, str, int]] = []
    for i in range(n_cols):
        column = align[:, i]
        counts = Counter(column)
        H = shannon_entropy_bits(counts, n_seqs)
        letter, count = counts.most_common(1)[0]
        column_stats.append((H, i, letter, count))
        print(f"Col {i:>2}  H={H:.4f}  most_common={letter} ({count}/{n_seqs})")

    print()
    print("Top 5 most-conserved columns (lowest entropy):")
    column_stats.sort(key=lambda row: (row[0], row[1]))
    for H, i, letter, count in column_stats[:5]:
        print(f"Col {i:>2}  '{letter}' frequency {count}/{n_seqs}")


if __name__ == "__main__":
    main()
