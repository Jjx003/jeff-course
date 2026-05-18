## Hints

The modern Biopython API (`Bio.Align.PairwiseAligner`) is what you want.
`Bio.pairwise2` still works but is deprecated as of Biopython 1.80.

Skeleton:

```python
from Bio import Align
from Bio.Align import substitution_matrices

aligner = Align.PairwiseAligner()
aligner.mode = "global"
aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
# Realistic affine gap penalties (BLOSUM62's `PairwiseAligner` defaults are
# 0 / 0 — free gaps — which produce nonsense alignments).
aligner.open_gap_score = -10
aligner.extend_gap_score = -1

alignments = aligner.align(seq_a, seq_b)
best = alignments[0]   # highest-scoring alignment

print(best)              # multi-line alignment block
print(best.score)        # numeric score
```

### Computing identity manually

The `Alignment` object's `.aligned` attribute gives you pairs of `(start,
end)` index ranges for each maximally-matched block, but extracting the
"identity %" is easier by walking the two aligned-with-gaps strings:

```python
# In Biopython ≥ 1.81, best[0] and best[1] are the two aligned sequences
# with `-` characters inserted at gap positions.
aligned_a = str(best[0])
aligned_b = str(best[1])

matches = sum(1 for a, b in zip(aligned_a, aligned_b)
              if a == b and a != "-")
total = len(aligned_a)  # alignment length including gaps
non_gap_columns = sum(1 for a, b in zip(aligned_a, aligned_b)
                      if a != "-" and b != "-")
```

Don't try to slice them out of `str(best)` directly — the modern
`PairwiseAligner` prints a three-line block with `target` / `query` labels
and index columns, not just the two raw sequences.

### Formatting

Required output format (header, alignment, blank line, then the
numeric fields):

```python
print(f"Aligning MB_fragment vs HBB_fragment")
print("Substitution matrix: BLOSUM62")
print("Mode: global")
print()
print("Alignment:")
print(best)                                       # multi-line block
print(f"Score: {best.score:.1f}")
print(f"Identity: {matches}/{non_gap_columns} ({100*matches/non_gap_columns:.1f}%)")
print(f"Alignment length: {len(aligned_a)}")
```

(The expected output rounds identity to one decimal, and the score uses
one decimal. Match these.)

## Common pitfalls

- **Sequence types.** Pass plain `str` objects to `aligner.align`, not
  `Seq` objects, to avoid version-specific surprises.
- **Multiple optimal alignments.** It's normal for `alignments` to have
  many entries with the same top score. Pick `alignments[0]`.
- **Identity denominators vary.** Some tools report identity over
  alignment length (with gaps), others over non-gap columns, others
  over the shorter sequence length. The expected output uses
  "non-gap columns" (positions where neither sequence has `-`).
- **Gap-score defaults** in Biopython's `PairwiseAligner` are
  `open_gap_score = 0`, `extend_gap_score = 0`. That gives free gaps and
  wild-looking alignments. **Override them** to the canonical BLAST values
  `-10` / `-1` so the alignment looks like a real BLOSUM62 alignment and
  is single-optimal.

## Things to try after

Once your output matches:

1. Switch `aligner.mode = "local"` and observe how the alignment block
   changes — local alignment trims the unaligned ends.
2. Try the Biopython defaults `aligner.open_gap_score = 0`,
   `aligner.extend_gap_score = 0` (free gaps). The alignment fragments
   itself into a mess as the solver inserts gaps wherever convenient —
   a useful negative example of why gap penalties exist.
3. Substitute the *full-length* MB and HBB sequences (not just fragments)
   and observe the identity number. Real human myoglobin and hemoglobin
   share about 25 % identity over the whole sequence — strong evidence
   of common ancestry from a shared globin ancestor.
4. Build your own scoring matrix where every match is +1 and every
   mismatch is $-1$ (or even simpler: use `aligner.match_score = 1` and
   `aligner.mismatch_score = -1` without a substitution matrix). This is
   essentially Levenshtein distance, and you'll see how much BLOSUM62
   helps.

Next module: scale up from two sequences to a whole *multiple sequence
alignment*, and use per-column entropy to surface the residues that
evolution refuses to touch.
