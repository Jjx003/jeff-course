## Goal

Given a small **multiple sequence alignment (MSA)** of six globin-like
sequences, compute and print:

1. The MSA dimensions (`N` sequences × `L` columns).
2. The **per-column Shannon entropy** in bits, the most common residue at
   that column, and how often it appears.
3. The **top 5 most-conserved columns** (lowest entropy), tied columns
   broken by ascending column index.

Use **Biopython** (`Bio.AlignIO`) to parse the embedded FASTA-style MSA
into a `MultipleSeqAlignment` object, then walk the columns yourself
with `align[:, col_idx]`. The entropy calculation is plain Python —
`collections.Counter` plus `math.log2`.

## Input

The starter file embeds the alignment as a multi-line string. Every
sequence is exactly 20 columns long (no gaps in this example):

```text
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
```

These are synthetic but globin-flavoured — most of them are tiny
mutations away from the same hypothetical ancestor. A real MSA from
HHblits or jackhmmer can have thousands of sequences and significant
gap content; we use a small toy MSA so the maths is checkable by hand.

![Protein multiple sequence alignment](https://commons.wikimedia.org/wiki/Special:Redirect/file/Protein_alignment.svg)

*A multiple sequence alignment turns related proteins into columns that can
be counted, compared, and scored for conservation. Image from Wikimedia
Commons, Nothingserious, public domain.*

## The conservation score

For column $i$, let $p_{a,i}$ be the fraction of sequences whose residue
at column $i$ is amino acid $a$. The **Shannon entropy** of that column,
in **bits**, is:

$$H_i = -\sum_{a} p_{a,i} \, \log_2 p_{a,i}$$

The sum runs over the residues that actually appear in the column. If
every sequence agrees, $H_i = 0$ (perfect conservation). If $k$ residues
appear with equal probability, $H_i = \log_2 k$ — its theoretical
maximum at that frequency profile.

Here are the entropy values you'll see for this MSA:

| Pattern in column | $H$ (bits) |
|---|---|
| 6 / 0 (perfectly conserved) | $0.0000$ |
| 5 / 1 split | $0.6500$ |
| 4 / 2 split | $0.9183$ |
| 4 / 1 / 1 split | $1.2516$ |

Check by hand on the 5/1 case: $H = -\tfrac{5}{6}\log_2\tfrac{5}{6} - \tfrac{1}{6}\log_2\tfrac{1}{6} \approx 0.6500$.

## Required output (exact)

```text
MSA: 6 sequences x 20 columns

Per-column Shannon entropy (bits):
Col  0  H=0.6500  most_common=V (5/6)
Col  1  H=0.0000  most_common=L (6/6)
Col  2  H=0.0000  most_common=S (6/6)
Col  3  H=0.6500  most_common=P (5/6)
Col  4  H=1.2516  most_common=A (4/6)
Col  5  H=0.0000  most_common=D (6/6)
Col  6  H=0.0000  most_common=K (6/6)
Col  7  H=0.6500  most_common=T (5/6)
Col  8  H=0.6500  most_common=N (5/6)
Col  9  H=0.0000  most_common=V (6/6)
Col 10  H=0.6500  most_common=K (5/6)
Col 11  H=0.0000  most_common=A (6/6)
Col 12  H=0.6500  most_common=A (5/6)
Col 13  H=0.0000  most_common=W (6/6)
Col 14  H=0.9183  most_common=G (4/6)
Col 15  H=0.0000  most_common=K (6/6)
Col 16  H=0.6500  most_common=V (5/6)
Col 17  H=1.2516  most_common=G (4/6)
Col 18  H=0.0000  most_common=A (6/6)
Col 19  H=0.0000  most_common=H (6/6)

Top 5 most-conserved columns (lowest entropy):
Col  1  'L' frequency 6/6
Col  2  'S' frequency 6/6
Col  5  'D' frequency 6/6
Col  6  'K' frequency 6/6
Col  9  'V' frequency 6/6
```

## What you should learn

- An MSA stacks evolutionarily related sequences so that *columns*
  represent homologous positions. Column statistics carry biological
  signal that single-sequence statistics never could.
- **Conservation $\Leftrightarrow$ structural / functional importance.**
  Columns with low entropy are positions that evolution has refused to
  tinker with — they're typically buried, catalytic, or critical for
  folding. The conserved `W` at column 13 above is a stand-in for the
  globin `WGK` motif, which sits at the start of the heme-binding
  pocket.
- Many ML methods for proteins (PSI-BLAST, GREMLIN, EVfold,
  AlphaFold2's MSA stack, ESMFold's implicit pretraining) all ultimately
  exploit MSA columns. Module 16 will show you the explicit "outer
  product mean" operation that AlphaFold2 uses to turn this kind of
  column statistic into structural predictions.
