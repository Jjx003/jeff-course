## Walkthrough

The whole solution is about 30 lines. The interesting bits:

### Parsing the MSA

```python
from io import StringIO
from Bio import AlignIO
align = AlignIO.read(StringIO(MSA_FASTA), "fasta")
```

`AlignIO.read` is the right call when you know the file contains exactly
one alignment record. Use `AlignIO.parse(...)` if you might have more
than one (e.g. a multi-block Stockholm file).

The returned `MultipleSeqAlignment` object supports both row indexing
(`align[i]` → a `SeqRecord`) and column slicing (`align[:, j]` → a
plain string of the residues at column `j`). The column slicing is the
killer feature here.

### The entropy helper

```python
def shannon_entropy_bits(counts, n):
    H = 0.0
    for count in counts.values():
        p = count / n
        H -= p * math.log2(p)
    return H
```

Two important details:

- We only iterate over `counts.values()`. `Counter` only contains
  residues actually present, so we never hit a `log2(0)`.
- We use `math.log2`, not `math.log`. The former gives bits, the
  latter gives nats. Bioinformatics convention is bits.

### Walking the columns

```python
for i in range(n_cols):
    column = align[:, i]              # e.g. 'VVMVVV'
    counts = Counter(column)
    H = shannon_entropy_bits(counts, n_seqs)
    letter, count = counts.most_common(1)[0]
    ...
```

`Counter.most_common(1)` returns a list of `(item, count)` tuples sorted
by descending count. We unpack the first one to get the most-frequent
residue and its count.

### Sorting for the top 5

```python
column_stats.sort(key=lambda row: (row[0], row[1]))
```

Two things to notice:

- The sort key is **`(entropy, col_idx)`**. Python's sort is stable
  and lexicographic over the tuple, so columns with equal entropy are
  broken by column index ascending. This is what makes the output
  deterministic.
- We sort *after* collecting all the rows. Sorting in-place during the
  loop would be O($L^2$) — pointless on a 20-column MSA but a habit
  to avoid on big alignments.

### Formatting

The exact output uses:

- `f"Col {i:>2}"` — right-align the column index to width 2 (so single
  digits get a leading space).
- `f"H={H:.4f}"` — entropy to 4 decimal places.
- Two spaces between the `Col NN` and the `H=` field.

Match these and the expected output diff is byte-for-byte identical.

## Reading the result

The five top-conserved columns are `L S D K V` at columns `1 2 5 6 9`.
This is the synthetic stand-in for the conserved start of a globin
fold's A-helix. In a real globin family alignment, you'd see the same
shape: long stretches of low entropy at structurally critical positions
(the heme-binding His, the F-helix kink, the proximal His, and the
WGK motif near the start of the E-helix), interspersed with surface
loops of high entropy where evolution has been free to wander.

The exercise was deliberately hand-built — six sequences is a tiny
sample size, and you can convince yourself by hand that "10 fully
conserved + 7 5-1 splits + 1 4-2 split + 2 4-1-1 splits" is what's
encoded above. On a real MSA with thousands of sequences, the entropy
distribution becomes a smooth U-shape with a clear separation between
"clearly conserved" and "clearly not conserved" columns, and the cutoff
you'd use to choose the "important" residues becomes obvious.
