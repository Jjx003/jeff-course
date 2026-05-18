## Goal

Parse a small embedded PDB structure with Biopython, extract every
**alpha-carbon coordinate** from chain A, and compute:

1. The number of CA atoms parsed (and the first three residues' names
   and sequence numbers as a sanity check).
2. The shape of the pairwise Euclidean distance matrix in Ångströms.
3. The **minimum non-zero** entry of that matrix (the closest CA-CA
   distance — should be ~3.8 Å for any sensible chain).
4. The **maximum** entry (the longest CA-CA distance — a rough proxy
   for the protein's size).
5. The number of **contacts**: residue pairs $(i, j)$ with $D_{ij} < 8\ \text{Å}$
   and $|i - j| \ge 2$. Excluding $|i - j| < 2$ removes trivial neighbours
   along the backbone — the contacts that survive are the structural
   ones.

## Input

The starter file embeds a small 10-residue **toy** structure as a PDB
string. Each residue is an alanine, and the alpha carbons are arranged
as a flat hairpin in the $xy$ plane:

```text
   y=3.8  R10  R9   R8   R7   R6
                                 |
   y=0.0  R1   R2   R3   R4   R5
          x=0  3.8  7.6  11.4 15.2
```

The chain runs $\text{R1} \to \text{R2} \to \dots \to \text{R5}$ along
the bottom row, then bends up at $\text{R6}$ and runs back
$\text{R6} \to \text{R10}$ along the top row. The two rows are stacked
3.8 Å apart in $y$ — close enough for many cross-row CA pairs to count
as contacts. This is structurally what a tiny **beta-hairpin** looks like
(without the hydrogen bonds that make a real one).

Use `Bio.PDB.PDBParser`:

```python
from io import StringIO
from Bio.PDB import PDBParser
parser = PDBParser(QUIET=True)
structure = parser.get_structure("toy", StringIO(PDB_STRING))
```

A `Structure` contains a list of `Model`s, each contains a list of
`Chain`s, each contains a list of `Residue`s, each contains a list of
`Atom`s. To grab CA atoms from chain A:

```python
chain = structure[0]["A"]
ca_atoms = [res["CA"] for res in chain
            if "CA" in res and res.id[0] == " "]
coords = np.array([atom.coord for atom in ca_atoms])
```

The `res.id[0] == " "` check filters out HETATM records (water, ligands,
ions). Our toy file has none, but the habit is worth picking up.

## Required output (exact)

```text
Parsed 10 alpha-carbons from chain A
First residues: ALA1, ALA2, ALA3
Distance matrix shape: (10, 10)
Min non-zero distance: 3.800 A
Max distance: 15.668 A
Number of contacts (d < 8.0 A, |i-j| >= 2): 18
```

Note the format of the residue summary: `<RESNAME><resnum>` with no
space.

## Why contacts matter

The **contact map** $C_{ij} = \mathbb{1}[D_{ij} < 8\ \text{Å}]$ is the
single most important intermediate representation in modern structure
prediction. AlphaFold2's pair representation is essentially a richer,
distance-binned version of a contact map. ESM-2's per-residue embeddings
implicitly encode the contact map as a learned similarity function.
Predicting "is residue 47 close to residue 142?" turns out to be nearly
equivalent to predicting the full 3D fold.

Two intuitions:

- A protein with many long-range contacts is **compact**.
- Pairs of residues that co-evolve in an MSA (module 7) are
  overwhelmingly more likely to be in contact in the folded structure.
  This is why MSA-based methods work.
