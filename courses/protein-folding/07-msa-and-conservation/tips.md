## Hints

1. Parse the embedded FASTA into a `MultipleSeqAlignment`:

```python
from io import StringIO
from Bio import AlignIO
align = AlignIO.read(StringIO(MSA_FASTA), "fasta")
n_seqs = len(align)
n_cols = align.get_alignment_length()
```

2. `align[:, i]` returns the residues at column `i` as a string. That
   string is exactly what you want to feed into `Counter`.

```python
from collections import Counter
column = align[:, i]              # e.g. 'VVMVVV'
counts = Counter(column)
```

3. Compute Shannon entropy in bits:

```python
import math
N = n_seqs
H = 0.0
for residue, n in counts.items():
    p = n / N
    H -= p * math.log2(p)
```

4. The most common residue is `counts.most_common(1)[0]` — a `(letter, count)`
   tuple.

5. For the "top 5 most-conserved columns" line, keep a list of
   `(entropy, col_idx, most_common_letter, most_common_count)` tuples,
   sort by `(entropy, col_idx)`, and take the first five.

6. The exact formatting matters. The expected output uses
   `Col {i:>2}  H={H:.4f}  most_common={letter} ({count}/{N})`. Pay
   attention to:
   - Right-align column index to width 2.
   - Two spaces between `Col NN` and the `H=` field.
   - Print entropy to 4 decimals.

## Sanity checks

- The 10 perfectly-conserved columns should have $H = 0$ exactly. If
  yours says `0.0000` you're fine; if it says `nan` you forgot to skip
  zero-probability terms (you can't take `log(0)` — but `Counter` only
  contains residues that *do* appear, so this shouldn't be an issue
  unless you explicitly iterate over all 20 amino acids).
- Total information content $\sum_i (\log_2 20 - H_i) \approx 76$ bits
  for this MSA. Don't print this; just a sanity check.
- The top-5 conservation list should contain `L S D K V` in column-index
  order: `1, 2, 5, 6, 9`. If you see `H W K V A` you're sorting only by
  entropy and not breaking ties consistently — check your sort key.

## Going deeper

- **HHblits** — [https://github.com/soedinglab/hh-suite](https://github.com/soedinglab/hh-suite). The most-used tool for building MSAs from a query against the UniRef HMM database. Output: a stockholm-format MSA you can convert to FASTA.
- **jackhmmer** — [http://hmmer.org/](http://hmmer.org/). The canonical iterative HMM search tool. AlphaFold2's MSA pipeline uses it (alongside HHblits).
- **MMseqs2** — [https://github.com/soedinglab/MMseqs2](https://github.com/soedinglab/MMseqs2). Massively faster than HHblits / jackhmmer, with similar recall. **ColabFold** uses MMseqs2 to build AlphaFold2-quality MSAs in seconds via [https://search.mmseqs.com/](https://search.mmseqs.com/).
- **Schneider & Stephens 1990** — *Sequence logos: a new way to display consensus sequences*. The original paper introducing sequence logos and the bits-of-information formulation.
- **PFAM** — [https://www.ebi.ac.uk/interpro/entry/pfam/](https://www.ebi.ac.uk/interpro/entry/pfam/). A curated database of pre-built MSAs for every known protein family. Each PFAM entry comes with a sequence logo computed from the family MSA.

## Things to try after

After your output matches:

1. Add a synthetic gap column (replace one residue per sequence with
   `-`) and observe how your entropy treats it. Compare strategies 1
   and 2 from the theory.
2. Compute the **frequency-of-most-common-residue** score and confirm
   it correlates closely with $-H$ in this small MSA — they'd diverge
   most for columns with three or more equally-frequent residues.
3. Pull a real PFAM entry's seed alignment (e.g. the globin family
   PF00042) and compute conservation across thousands of sequences. The
   E-helix region you saw in module 6 should jump out as a long stretch
   of low entropy.

Next module: parsing real 3-D structures from PDB files.
