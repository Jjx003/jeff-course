"""
Reference solution for module 05.
"""

import io
from collections import Counter

from Bio import SeqIO

FASTA = """\
>sp|P02144|MYG_HUMAN Myoglobin OS=Homo sapiens OX=9606 GN=MB
MGLSDGEWQLVLNVWGKVEADIPGHGQEVLIRLFKGHPETLEKFDKFKHLKSEDEMKASE
DLKKHGATVLTALGGILKKKGHHEAEIKPLAQSHATKHKIPVKYLEFISECIIQVLQSKH
PGDFGADAQGAMNKALELFRKDMASNYKELGFQG
"""

STANDARD_AA = "ACDEFGHIKLMNPQRSTVWY"
HYDROPHOBIC = set("AVLIMFW")


def main() -> None:
    records = list(SeqIO.parse(io.StringIO(FASTA), "fasta"))
    record = records[0]

    seq = str(record.seq).upper()
    length = len(seq)

    print(f"Header: {record.description}")
    print(f"Length: {length}")
    print()
    print("Composition:")

    counts = Counter(seq)
    for aa in sorted(STANDARD_AA):
        count = counts.get(aa, 0)
        pct = 100.0 * count / length
        print(f"  {aa}: {count:>3} ({pct:>5.1f}%)")

    most_letter, most_count = counts.most_common(1)[0]
    print()
    print(f"Most frequent: {most_letter} (count {most_count})")

    hydro_count = sum(counts[a] for a in HYDROPHOBIC)
    hydro_pct = 100.0 * hydro_count / length
    print(f"Hydrophobic fraction (AVLIMFW): {hydro_pct:>5.1f}%")


if __name__ == "__main__":
    main()
