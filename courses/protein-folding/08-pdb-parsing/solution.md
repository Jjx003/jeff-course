## Walkthrough

### Parsing

```python
parser = PDBParser(QUIET=True)
structure = parser.get_structure("toy", StringIO(PDB_STRING))
chain = structure[0]["A"]
```

`QUIET=True` is the right default for clean scripts — Biopython is
otherwise quite vocal about minor formatting quirks. `structure[0]`
indexes the first model (the only one in our file); `["A"]` picks the
chain. The chain object is iterable in residue order.

### Filtering CA atoms

```python
ca_atoms = [res["CA"] for res in chain
            if res.id[0] == " " and "CA" in res]
```

Two filters:

- `res.id[0] == " "` keeps standard amino-acid residues (`hetflag` is
  `" "` for them). Waters, ligands, and modified residues have other
  hetflag values like `"W"` or `"H_<NAME>"`.
- `"CA" in res` skips residues that happen to be missing their alpha
  carbon (rare in well-resolved structures, but it does happen with
  partially disordered residues).

### Pairwise distance matrix

```python
coords = np.array([atom.coord for atom in ca_atoms])  # (N, 3)
diffs = coords[:, None, :] - coords[None, :, :]       # (N, N, 3)
D = np.linalg.norm(diffs, axis=-1)                    # (N, N)
```

The broadcasting trick is worth absorbing: by adding length-1 axes in
different positions, we get an outer-product-like difference between
all pairs. `np.linalg.norm(..., axis=-1)` reduces over the 3-vector
component to give a scalar distance per pair.

### Counting contacts

```python
idx = np.arange(n)
sep = np.abs(idx[:, None] - idx[None, :])           # (N, N) sequence sep
contact_mask = (D < 8.0) & (sep >= 2)
n_contacts = int(np.triu(contact_mask).sum())
```

Two boolean masks ANDed together. `np.triu` keeps only the upper
triangle (excluding the diagonal by default), which avoids
double-counting since `D` and `contact_mask` are symmetric. An
equivalent expression: `int(contact_mask.sum() // 2)` — works because
the diagonal is zero in the contact mask (sep is 0 there) and every
off-diagonal pair appears twice.

## Sanity checking the toy answer

The structure has $N = 10$ residues, two parallel rows of 5 stacked
3.8 Å apart. Let's verify the contact count by hand:

**Within each row** (5 residues, $|i - j| = 2$ gives $D = 7.6 < 8$):
- Row 1: 3 pairs (1-3, 2-4, 3-5).
- Row 2: 3 pairs (6-8, 7-9, 8-10).
- $|i - j| = 3$ within a row gives $D = 11.4$ — not a contact.

**Across rows** (any pair $i \in \{1..5\}, j \in \{6..10\}$ with
$|i - j| \ge 2$ and $D < 8$):
- 1-9: $\sqrt{3.8^2 + 3.8^2} = 5.37$ ✓
- 1-10: $3.8$ ✓
- 2-8: $5.37$ ✓
- 2-9: $3.8$ ✓
- 2-10: $5.37$ ✓
- 3-7: $5.37$ ✓
- 3-8: $3.8$ ✓
- 3-9: $5.37$ ✓
- 4-6: $5.37$ ✓
- 4-7: $3.8$ ✓
- 4-8: $5.37$ ✓
- 5-7: $5.37$ ✓

That's 12 cross-row contacts plus 6 within-row contacts = **18** in
total. Matches the printed answer.

The borderline case is the pair (3, 6): distance $\sqrt{7.6^2 + 3.8^2} = \sqrt{72.2} \approx 8.497$, which is just above the 8 Å cutoff and excluded.

### Min and max

- **Min non-zero**: 3.800 Å. There are many adjacent pairs at this
  distance — every $(i, i\pm 1)$ within a row, plus the kink pair
  (5, 6), plus the cross-row stacks (1, 10) and (5, 6).
- **Max**: $\sqrt{15.2^2 + 3.8^2} = \sqrt{245.48} \approx 15.668$ Å,
  achieved by the diagonally-opposite pairs (1, 6) and (5, 10).

## Reading the contact map

Even on this toy hairpin, the contact pattern carries the structural
signal:

- The within-row diagonal contacts ($i, i+2$) tell you each row is a
  short, extended strand.
- The cross-row anti-diagonal contacts (e.g. 1-10, 2-9, 3-8) tell you
  the two strands are stacked anti-parallel — the hallmark of a
  beta-hairpin.

A real $L \times L$ contact map of a real protein is far busier, but
the pattern recognition is the same. AlphaFold2's pair representation
(modules 15-16) is essentially a high-dimensional generalisation of
this contact-map view.
