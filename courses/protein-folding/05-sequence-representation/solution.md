## Walkthrough

The whole solution is a handful of lines. The interesting bits are:

### Parsing the embedded FASTA

`SeqIO.parse` wants a file-like object. To use it on a string literal we
wrap with `io.StringIO`:

```python
records = list(SeqIO.parse(io.StringIO(FASTA), "fasta"))
record = records[0]
```

The result is a `SeqRecord`. `record.description` is the full header line
*without* the leading `>` (SeqIO strips it for you).

### Counting

`collections.Counter` is the right tool: linear-time, single-pass, gives you
a dict-like object indexed by residue letter.

```python
counts = Counter(str(record.seq).upper())
```

We `.upper()` defensively even though our input is already uppercase, in
case the script is reused.

### Formatting the table

The key formatting trick is the f-string spec `{count:>3}` (right-align
to width 3) and `{pct:>5.1f}` (right-align to width 5 with one decimal
place). Get these right and the expected output matches byte-for-byte.

```python
for aa in sorted(STANDARD_AA):
    count = counts.get(aa, 0)
    pct = 100.0 * count / length
    print(f"  {aa}: {count:>3} ({pct:>5.1f}%)")
```

`STANDARD_AA = "ACDEFGHIKLMNPQRSTVWY"` already alphabetises after `sorted()`.

### Most frequent + hydrophobic fraction

`Counter.most_common(n)` returns a list of `(letter, count)` tuples sorted
by count, descending. Take the first.

The hydrophobic fraction is a one-line sum over the canonical set
`{A, V, L, I, M, F, W}`. Real proteins use a few different hydrophobic
sets depending on the analysis — Kyte-Doolittle, Eisenberg, etc. — but
this one is the most commonly cited.

## Sanity check the numbers

For human myoglobin:

- Length 154 — matches the standard UniProt entry.
- Lysine `K` is by far the most common residue. Myoglobin is famously
  lysine-rich, which contributes to its high pI and high solubility.
- ~38 % hydrophobic — completely typical for a small globular protein
  designed to live in the cytoplasm of a muscle cell.

If your numbers are off, the usual cause is including the header line in
the sequence count, or forgetting to strip newlines from the wrapped
sequence lines. `SeqIO` handles both for free if you use it correctly.
