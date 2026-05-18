## Goal

Parse the FASTA-formatted text below for **human myoglobin** and produce a
summary of its amino-acid composition.

Specifically, your script must print:

1. The sequence's UniProt header line (the first line, starting with `>`).
2. The sequence length (number of residues).
3. The **count** and **percentage** of each of the 20 standard amino acids,
   sorted alphabetically by one-letter code. Percentages rounded to one
   decimal place.
4. The single most-frequent amino acid (its letter and its count).
5. The fraction of **hydrophobic** residues (`A V L I M F W`), printed to
   one decimal place as a percentage.

Use **Biopython** (`from Bio import SeqIO`) to do the parsing. Don't write
your own FASTA parser.

## Input

The starter file embeds the FASTA as a string literal. You parse it with
`SeqIO.parse(io.StringIO(fasta), 'fasta')`.

```text
>sp|P02144|MYG_HUMAN Myoglobin OS=Homo sapiens OX=9606 GN=MB
MGLSDGEWQLVLNVWGKVEADIPGHGQEVLIRLFKGHPETLEKFDKFKHLKSEDEMKASE
DLKKHGATVLTALGGILKKKGHHEAEIKPLAQSHATKHKIPVKYLEFISECIIQVLQSKH
PGDFGADAQGAMNKALELFRKDMASNYKELGFQG
```

## Expected output (exact)

```text
Header: sp|P02144|MYG_HUMAN Myoglobin OS=Homo sapiens OX=9606 GN=MB
Length: 154

Composition:
  A:  12 (  7.8%)
  C:   1 (  0.6%)
  D:   8 (  5.2%)
  E:  14 (  9.1%)
  F:   7 (  4.5%)
  G:  15 (  9.7%)
  H:   9 (  5.8%)
  I:   8 (  5.2%)
  K:  20 ( 13.0%)
  L:  17 ( 11.0%)
  M:   4 (  2.6%)
  N:   3 (  1.9%)
  P:   5 (  3.2%)
  Q:   7 (  4.5%)
  R:   2 (  1.3%)
  S:   7 (  4.5%)
  T:   4 (  2.6%)
  V:   7 (  4.5%)
  W:   2 (  1.3%)
  Y:   2 (  1.3%)

Most frequent: K (count 20)
Hydrophobic fraction (AVLIMFW):  37.0%
```

## What you should learn

- FASTA is just `>header\n SEQUENCE \n`. Real-world FASTA files often
  contain many records and lines wrapped at 60–80 columns.
- Biopython's `SeqIO` gives you a `SeqRecord` whose `.seq` attribute is a
  `Seq` object — a string-like wrapper that knows it represents biological
  sequence.
- Counting amino acids is just `collections.Counter(str(seq))`. The
  `ProteinAnalysis` class in `Bio.SeqUtils.ProtParam` can do this and a
  lot more (molecular weight, isoelectric point, aromaticity) — but for
  this exercise stick to plain `Counter` so you can see the pieces.
- **Hydrophobicity matters.** ~38 % hydrophobic is typical for a globular
  protein; remember the hydrophobicity rule from module 1.
