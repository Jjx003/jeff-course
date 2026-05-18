"""
Parse a FASTA-formatted protein sequence with Biopython and print a
composition summary. See problem.md for the exact expected output format.
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
    # TODO 1: Parse FASTA with SeqIO.parse(io.StringIO(FASTA), 'fasta').
    #         Pull out the single SeqRecord.
    record = ...

    # TODO 2: Print the header (record.description) and length.

    # TODO 3: Count amino acids with Counter(str(record.seq)).

    # TODO 4: Print the composition table, sorted alphabetically.
    #         Use f-string formatting: f"  {aa}: {count:>3} ({pct:>5.1f}%)"

    # TODO 5: Print the most-frequent amino acid.

    # TODO 6: Print the hydrophobic fraction (residues in HYDROPHOBIC).


if __name__ == "__main__":
    main()
