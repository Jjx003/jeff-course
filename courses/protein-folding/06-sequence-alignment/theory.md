## What an alignment actually is

A pairwise alignment of two sequences `s` and `t` is a way to rewrite them
with gap symbols (`-`) inserted such that:

- Both rewritten strings have the same length.
- Reading down the columns lines up "corresponding" residues.

For example:

```text
s: M K T A Y G L S E R N
t: M - T A Y G L T E R N
```

Here `t` has a gap at position 2 (a deletion relative to `s`), and a
substitution `S → T` at position 8. The aligned length is 11; the
"identity" is the number of columns where both strings have the same
letter (`M`, `T`, `A`, `Y`, `G`, `L`, `E`, `R`, `N` — 9 out of 11 non-gap
columns).

## Substitution matrices: BLOSUM62

Not all mismatches are equally bad. Substituting one hydrophobic residue
for another (`L → I`) is a much smaller change than substituting a
positive for a negative residue (`K → D`). The classical way to encode
this is with a **substitution matrix**.

**BLOSUM62** (BLOcks SUbstitution Matrix, with 62 in the name referring
to the sequence-identity threshold used when building it) is the
canonical protein scoring matrix. It's a $20 \times 20$ table of log-odds
scores:

$$S_{ab} = \frac{1}{\lambda} \log_2 \frac{P_{ab}}{f_a f_b}$$

where $P_{ab}$ is the observed frequency of aligned $(a, b)$ pairs in
trusted alignments of moderately-related proteins, and $f_a$, $f_b$ are
the background frequencies of each amino acid. Positive scores mean
"more common than chance"; negative scores mean "rarely observed in
related proteins".

Some example entries (rounded to integers, as in the standard matrix):

| | A | L | K | D |
|---|---|---|---|---|
| A | 4 | -1 | -1 | -2 |
| L | -1 | 4 | -2 | -4 |
| K | -1 | -2 | 5 | -1 |
| D | -2 | -4 | -1 | 6 |

A perfect match gets the diagonal score (~4–11). Mismatches between
similar residues are mildly negative (`A`/`L`: $-1$). Mismatches between
chemically very different residues are strongly negative (`L`/`D`: $-4$).

This matrix is what powers BLAST, PSI-BLAST, and most classical protein
alignment tools. Biopython provides it as `Bio.Align.substitution_matrices.load("BLOSUM62")`.

## Gap penalties: opening and extension

Inserting a gap costs score. Standard "affine" gap penalties separate:

- **Gap open** — fixed cost for starting a new gap.
- **Gap extend** — per-residue cost for extending an existing gap.

Typical values for protein BLOSUM62 alignment are gap-open = $-10$ to $-12$
and gap-extend = $-1$ to $-2$. The intuition: a single contiguous gap of
length $k$ should be much cheaper than $k$ separate single-residue gaps,
because indel mutations tend to happen in bursts.

In Biopython's modern API:

```python
aligner = Align.PairwiseAligner()
aligner.substitution_matrix = matlist.load("BLOSUM62")
aligner.open_gap_score = -10
aligner.extend_gap_score = -1
```

Note that the Biopython defaults are `open_gap_score = 0` and
`extend_gap_score = 0` — i.e. *free gaps*. Always override them for
real protein alignment work; the exercise uses `-10 / -1`.

## Global vs local alignment

Two flavours:

- **Global (Needleman–Wunsch, 1970)** — find the best alignment
  spanning the *entire* length of both sequences. Best for comparing
  homologous proteins of similar length.
- **Local (Smith–Waterman, 1981)** — find the best-scoring **substring**
  alignment. Best for finding shared domains within longer sequences.

Biopython selects mode with `aligner.mode = "global"` or `"local"`.
For evolutionarily related, similar-length proteins, global is the right
default. BLAST uses a sophisticated local-alignment heuristic for
database searches.

## Edit distance: the simpler cousin

Substitution-matrix alignment is the bioinformatician's version of a
more general computer-science concept: **edit distance** (also called
**Levenshtein distance**). Edit distance asks: what is the *minimum
number* of single-character edits (insertions, deletions, substitutions)
needed to transform one string into another?

The classical DP recurrence:

$$
D[i, j] = \min \begin{cases}
D[i-1, j] + 1 & \text{(deletion)} \\
D[i, j-1] + 1 & \text{(insertion)} \\
D[i-1, j-1] + \mathbb{1}[s_i \neq t_j] & \text{(match or substitution)}
\end{cases}
$$

with base cases $D[0, j] = j$ and $D[i, 0] = i$. Time $O(mn)$, space
$O(mn)$ (reducible to $O(\min(m, n))$ with a rolling array).

This is exactly what Needleman–Wunsch does with **unit costs**. Replace
"+1 for substitution" with "minus BLOSUM62 score" and "+1 for gap" with
"gap penalty", and you have protein global alignment.

## The bridge to transformers

Why bring up alignment in a course about modern protein ML? Because
**transformer attention is essentially a continuous, learned version of
sequence alignment**. We'll spend module 10 unpacking this idea, but
here's the seed:

- Alignment asks "given these two sequences, which positions correspond
  to each other?" with discrete operations.
- Attention asks "for each position in this sequence, which other
  positions contain information that should be incorporated here?" with
  continuous, learned similarity scores.

Both are similarity-mining algorithms over sequences. Both ultimately
serve the same purpose in protein ML: figure out which residues in a
known related sequence inform predictions about an unknown residue.
Alignment does this *explicitly* with database hits; attention does it
*implicitly* with weights learned from millions of pretraining sequences.

## Limitations of pairwise alignment

Pairwise alignment is fast and accurate for *closely* related sequences
(say, > 30 % identity). It degrades at lower identities because the
BLOSUM scores get noisier — there's not enough conserved signal to
overwhelm random mismatches. Below 20 % identity (the "twilight zone"),
pairwise alignment often misses real homology.

The fix is to use *more* sequences: build a **multiple sequence
alignment** of many homologs and look for consensus patterns. That's the
topic of module 7.
