## Hints

1. The starter file already has `from Bio import SeqIO` and `import io`.
   Wrap the FASTA string in `io.StringIO`, pass to `SeqIO.parse`, and
   take `list(...)[0]`.

2. `record.description` gives you the full header. **The expected output
   strips the leading `>`** — `SeqIO` already does this for you, so just
   print `record.description` directly.

3. For counts, `collections.Counter(str(record.seq))` is one line.

4. For formatting:

```python
for aa in sorted("ACDEFGHIKLMNPQRSTVWY"):
    count = counts.get(aa, 0)
    pct = 100.0 * count / length
    print(f"  {aa}: {count:>3} ({pct:>5.1f}%)")
```

   Mind the exact spacing — `:>3` right-aligns the count to 3 chars,
   `:>5.1f` right-aligns the percentage to 5 chars including the decimal.

5. For "most frequent": `counts.most_common(1)[0]` returns a `(letter,
   count)` tuple.

6. Hydrophobic fraction:

```python
HYDRO = set("AVLIMFW")
hydro_count = sum(counts[a] for a in HYDRO)
hydro_pct = 100.0 * hydro_count / length
```

## Sanity checks

- The 20 individual amino-acid counts should sum to the sequence length
  (myoglobin contains only the 20 standard amino acids — no `X`, no
  selenocysteine).
- Sum of all 20 percentages should round to 100.0 %.
- The most-frequent residue in human myoglobin should be lysine (`K`)
  with 20 copies. If you get something else, you're probably not
  uppercasing the sequence or you have an off-by-one error somewhere.

## Variations to try

After you've got the exact expected output, mess around:

- Compute and print the **molecular weight** in Daltons using
  `ProteinAnalysis(...).molecular_weight()`. (Should be around 17,200 Da
  for human myoglobin.)
- Compute the **GRAVY** score using `.gravy()`. Negative — confirms
  myoglobin is soluble.
- Compute the **isoelectric point** with `.isoelectric_point()`. Around
  pH 7.4 for myoglobin.
- Try swapping in the sequence of a known *membrane* protein (e.g.
  bacteriorhodopsin) and watch the hydrophobic fraction jump above 50 %.

Next module: pairwise sequence alignment — compare two real protein
sequences with BLOSUM62 and see how `MGLSDGEW...` lines up against a
distant evolutionary cousin.
