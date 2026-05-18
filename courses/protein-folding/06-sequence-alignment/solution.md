## Walkthrough

The solution is short — most of the cleverness lives in Biopython.

### Setting up the aligner

```python
aligner = Align.PairwiseAligner()
aligner.mode = "global"
aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
aligner.open_gap_score = -10
aligner.extend_gap_score = -1
```

`PairwiseAligner` is the modern API (added in Biopython 1.72; `pairwise2`
is deprecated). Loading `BLOSUM62` as the substitution matrix
automatically gives you sensible diagonal scores for matches and reasonable
penalties for mismatches.

We **must** override the gap scores — Biopython's defaults are
`open_gap_score = 0` and `extend_gap_score = 0`, i.e. *free gaps*.
With free gaps the global aligner happily shatters the alignment into
single-residue islands separated by gap runs, inflating the score and
identity but producing a nonsense block. The values `-10` / `-1` are the
canonical BLAST-style gap penalties for BLOSUM62; with them this
particular pair has a single optimal alignment and the printed block is
clean.

### Reading the alignment

```python
alignments = aligner.align(MB_FRAGMENT, HBB_FRAGMENT)
best = alignments[0]
```

`alignments` is a lazy iterator over *all* optimal alignments tied at
the top score. We just take the first.

`best[0]` and `best[1]` are the two aligned sequences as strings with
`-` for gaps. `len(best[0]) == len(best[1])` is always true after
alignment.

### Identity computation

Two denominators are common in the literature:

- **Identity over alignment length** — counts gap columns against you.
- **Identity over non-gap columns** — only positions where both
  sequences contributed a residue.

We use the second (more common when reporting "% identity" between
two sequences). The numerator is positions where both sides agree.

### Printing

`print(str(best), end="")` — the `Alignment` object's `str()` already
ends in a newline, so we suppress `print`'s extra one to avoid a blank
line before the score.

The numeric formatting `{best.score:.1f}` matches the expected output
to one decimal place.

## Reading the result

The two fragments share `10 / 30 ≈ 33 %` identity over the aligned
non-gap columns. That's within the "obviously related" range, which is
consistent with the biology — myoglobin and the hemoglobin beta chain
both come from the **globin family** and share a common ancestor that
existed roughly 600 million years ago.

Notice the **`WGKV`** motif near the middle of both sequences (columns
14–17 of the alignment, all four positions match). This is the conserved
beginning of the **E-helix**, a structurally critical piece of every
globin fold. Conserved motifs like this are the fingerprints evolution
leaves behind, and they're the signal that MSA-based methods exploit
(next module).
