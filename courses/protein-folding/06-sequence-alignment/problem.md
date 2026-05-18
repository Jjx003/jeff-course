## Goal

Align two short, real protein sequences using Biopython's
`Bio.Align.PairwiseAligner` and print:

1. The best-scoring **global alignment** under the BLOSUM62 substitution
   matrix.
2. The alignment score.
3. The **sequence identity** — the percentage of aligned columns where the
   two sequences contain the same residue.
4. The **alignment length** (including gaps).

The two sequences are short N-terminal fragments of human **myoglobin**
(`MB`) and human **hemoglobin beta chain** (`HBB`). They share evolutionary
ancestry (both are oxygen-binding heme proteins) and you should be able to
see the relationship in the alignment.

Sequences (provided in the starter):

```text
MB_fragment : MGLSDGEWQLVLNVWGKVEADIPGHGQEVL
HBB_fragment: VHLTPEEKSAVTALWGKVNVDEVGGEALGRL
```

## Expected output

Use BLOSUM62 with affine gap penalties `open=-10`, `extend=-1` (the
canonical BLAST-style choice). With those penalties there is a single
optimal alignment for these fragments and the run should print something
like:

```text
Aligning MB_fragment vs HBB_fragment
Substitution matrix: BLOSUM62
Mode: global

Alignment:
target            0 MGLSDGEWQLVLNVWGKVEAD-IPGHGQEVL 30
                  0 ..|...|...|...||||..|-..|.....| 31
query             0 VHLTPEEKSAVTALWGKVNVDEVGGEALGRL 31
Score: 30.0
Identity: 10/30 (33.3%)
Alignment length: 31
```

Note that the exact textual layout of the alignment block (the `target` /
`query` labels, the index columns, and the match line) is produced by
Biopython's `print(alignment)` and may shift slightly across Biopython
versions. Because of that this module has **no auto-graded reference
output** — Submit returns a `pending` verdict and you can eyeball the
numeric summary lines yourself.

The four numeric fields to verify are:

- **Score**: `30.0`
- **Identity**: `10 / 30` non-gap columns = `33.3%`
- **Alignment length**: `31` (including the one gap)
- The aligned `MB_fragment` row contains a single `-` gap that absorbs the
  one-residue length difference vs `HBB_fragment`.

## What you should learn

- An **alignment** is a way of writing two sequences with `–` gaps so the
  positions that "go with each other" are stacked vertically.
- The **score** is a sum of per-column scores from a **substitution matrix**
  (BLOSUM62 by default for proteins) minus gap penalties.
- **Sequence identity** is the headline number: percentage of aligned
  positions that are exactly equal. Higher = more closely related.
- The classical algorithms are **Needleman-Wunsch** (global) and
  **Smith-Waterman** (local). Biopython's `PairwiseAligner` does both,
  set by `aligner.mode`.
- Alignment is the discrete cousin of the **continuous "fuzzy matching"**
  that transformer attention performs (module 10). Both ask "how similar
  are these two sequences?" — one with hard scoring, one with learned
  vectors.
