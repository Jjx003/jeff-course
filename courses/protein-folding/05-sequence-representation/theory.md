## FASTA in 30 seconds

FASTA is the universal text format for biological sequences. The grammar
fits on a postcard:

```text
>header line, free-form text after the >
SEQUENCE LINE 1
SEQUENCE LINE 2
SEQUENCE LINE 3
>second record's header
ITS SEQUENCE
```

Rules:

- The first character of each record is `>`.
- The header line is free-form. By convention, UniProt headers look like
  `>sp|ACCESSION|NAME OS=organism OX=taxid GN=gene` — `sp` for SwissProt,
  `tr` for TrEMBL.
- The sequence wraps onto multiple lines. Concatenating them gives the
  actual sequence.
- Whitespace and case are ignored when parsing.

Most large databases (UniProt, NCBI nr, BFD, MGnify) distribute their
sequences as one giant FASTA file (often gzipped). A single FASTA file
with hundreds of millions of records is normal.

## Biopython's SeqIO and SeqRecord

Biopython's `Bio.SeqIO` is the standard parser. Its main idiom:

```python
from Bio import SeqIO

for record in SeqIO.parse('myfile.fasta', 'fasta'):
    print(record.id)         # accession (parsed from header)
    print(record.description) # full header line (minus the leading >)
    print(str(record.seq))    # the sequence as a string
    print(len(record.seq))    # length
```

Each iteration yields a **`SeqRecord`**:

- `record.id` — parsed identifier (first whitespace-separated token of
  the header).
- `record.description` — the rest of the header.
- `record.seq` — a **`Seq`** object, which acts like a string but knows
  it's biological. Convert to a plain string with `str(record.seq)`.
- `record.annotations` — extra metadata parsed from the header (more
  populated for GenBank/EMBL formats than for plain FASTA).

If you have the FASTA as a string (e.g. baked into the script), wrap it
in `io.StringIO`:

```python
import io
from Bio import SeqIO
records = list(SeqIO.parse(io.StringIO(fasta_string), 'fasta'))
```

## Computing composition

The simplest approach is `collections.Counter`:

```python
from collections import Counter
counts = Counter(str(record.seq))
counts['L']  # how many leucines
```

For a more biology-aware analysis, use `Bio.SeqUtils.ProtParam`:

```python
from Bio.SeqUtils.ProtParam import ProteinAnalysis

pa = ProteinAnalysis(str(record.seq))
pa.get_amino_acids_percent()  # dict like {'A': 0.078, 'C': 0.006, ...}
pa.molecular_weight()         # in Daltons
pa.isoelectric_point()        # pI
pa.aromaticity()              # fraction of F + Y + W
pa.gravy()                    # Grand Average of Hydrophobicity
```

For this module's exercise we stick to plain `Counter` because it makes
the formatting requirements explicit.

## Why hydrophobicity matters

We saw in module 1 that hydrophobic residues drive folding (they cluster
in the core, away from water). The **GRAVY score** (Grand Average of
Hydropathy) is a single number summarising this:

$$\text{GRAVY} = \frac{1}{L} \sum_{i=1}^{L} \text{hydropathy}(x_i)$$

where the per-residue hydropathy is the **Kyte-Doolittle** scale. Positive
GRAVY means net hydrophobic (membrane proteins often score $> 0$);
negative GRAVY means net hydrophilic (soluble globular proteins typically
score $-0.5$ to $0$).

Myoglobin is a soluble globular protein, so its GRAVY is mildly negative
(around $-0.4$). Our "hydrophobic fraction" calculation in the exercise
is a simpler proxy — just the fraction of residues in the canonical
hydrophobic set `{A, V, L, I, M, F, W}`. About 35–40 % is typical for a
soluble globular protein.

## Common gotchas

- **Don't forget `str()`** when you index or count a `Seq` object —
  Biopython makes this work via `__iter__` but explicit conversion to
  `str` avoids surprises.
- **Case sensitivity** — some FASTA files use lowercase letters to mean
  "soft-masked" residues (low-complexity regions). Always `.upper()`
  before counting.
- **Non-standard letters** — real-world sequences sometimes contain
  `X` (any), `B`, `Z`, `*` (stop codon), `-` (alignment gap). Decide
  upfront whether your code skips, errors, or counts them.
- **Header parsing** — Biopython treats only the first whitespace-
  separated token of the header as the `id`. Some FASTA files have
  semicolon-separated headers or other quirks; for serious work, parse
  the header yourself if needed.

## Real-world FASTA workflows

In real protein ML:

- **Inputs to a model** are usually a single sequence (or a batch of
  short sequences) loaded from a small FASTA file or a database query.
- **MSAs** are stored as multi-record FASTA where every record has the
  same alignment length (gaps shown as `-`).
- **Pretraining datasets** for PLMs are millions or billions of records.
  At that scale you usually use a binary format (HDF5, LMDB,
  Arrow/Parquet) and only convert to/from FASTA at the edges.

Biopython is the right tool for small/medium files (up to a few GB) and
for one-off scripts. For pretraining-scale data, switch to
`pyfastx`, `seqkit`, or custom binary loaders.
