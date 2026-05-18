## Hints

1. Parse the embedded PDB string with a `StringIO` wrapper:

```python
from io import StringIO
from Bio.PDB import PDBParser
parser = PDBParser(QUIET=True)   # QUIET=True hides "discontinuous chain" warnings
structure = parser.get_structure("toy", StringIO(PDB_STRING))
chain = structure[0]["A"]
```

2. Filter for standard residues with a CA atom. Use the `res.id` triple
   `(hetflag, resseq, icode)` and check `hetflag == " "`:

```python
ca_atoms = [res["CA"] for res in chain
            if res.id[0] == " " and "CA" in res]
```

3. Stack the coords into one $(N, 3)$ NumPy array:

```python
import numpy as np
coords = np.array([atom.coord for atom in ca_atoms])  # shape (N, 3)
```

4. Vectorised pairwise distance matrix:

```python
diffs = coords[:, None, :] - coords[None, :, :]   # (N, N, 3)
D = np.linalg.norm(diffs, axis=-1)                # (N, N)
```

5. Min non-zero distance — the diagonal is 0, so mask it out:

```python
mask = ~np.eye(len(coords), dtype=bool)
min_nonzero = D[mask].min()
```

6. Contacts: the "exclude $|i - j| < 2$" rule is easiest with a
   broadcast index difference:

```python
idx = np.arange(N)
sequence_separation = np.abs(idx[:, None] - idx[None, :])
contact_mask = (D < 8.0) & (sequence_separation >= 2)
n_contacts = int(contact_mask.sum() // 2)   # // 2 because the matrix is symmetric
```

7. Format strings: the expected output uses `.3f` for distances and a
   plain integer for the contact count. Use `f"{val:.3f} A"` (with an
   ASCII `A` instead of `Å`, to avoid encoding hassles in the grader).

## Sanity checks

- The 10 alpha carbons should be at exactly the coordinates listed in
  problem.md. Print `coords` if anything looks off.
- The matrix is symmetric: `np.allclose(D, D.T)` should be `True`.
- The diagonal is exactly zero: `np.allclose(np.diag(D), 0)` should be
  `True`.
- A sanity-counting trick: every row of the contact mask should have
  the same count as the corresponding column (because the mask is
  symmetric). Sum-and-halve is fine.

## Going deeper

- **RCSB PDB** — [https://www.rcsb.org/](https://www.rcsb.org/). Search by PDB ID, sequence, or structure. Each entry has an interactive 3D viewer, the raw `.pdb` and `.cif` files, and an "FASTA download" button.
- **PDB-101** — [https://pdb101.rcsb.org/](https://pdb101.rcsb.org/). RCSB's educational site. Excellent for grounding the abstract bits of this module in real molecules.
- **Biopython PDB module** — [https://biopython.org/wiki/The_Biopython_Structural_Bioinformatics_FAQ](https://biopython.org/wiki/The_Biopython_Structural_Bioinformatics_FAQ). The official documentation; covers PDB / mmCIF parsing, residue selection, structural superposition, DSSP integration.
- **biotite** — [https://www.biotite-python.org/](https://www.biotite-python.org/). A modern alternative with a NumPy-native data structure and a much faster parser. Recommended for ML pipelines.
- **mmCIF format reference** — [https://mmcif.wwpdb.org/](https://mmcif.wwpdb.org/). The official spec for the PDB's modern format.

## Things to try after

After the basic output works:

1. **Plot the distance map.** `plt.imshow(D, cmap='viridis')` and
   `plt.imshow(D < 8, cmap='gray_r')` for a quick visualisation.
   The hairpin structure should be obvious as the perpendicular
   anti-diagonal stripe.
2. **Try a real structure.** Use `Bio.PDB.PDBList().retrieve_pdb_file("1UBQ")`
   to download ubiquitin (76 residues), parse it, and run the same
   analysis. Min CA-CA distance in a real protein is a remarkably
   consistent ~3.8 Å. Max is bounded by the protein's overall size —
   ~30 Å for ubiquitin.
3. **Switch to heavy-atom contacts.** Instead of CA-CA distances,
   compute the minimum *over all heavy atoms* of residues $i$ and $j$.
   This is the contact definition used by some tools (it captures
   side-chain proximity that CA-CA misses).
4. **Compare formats.** Repeat the exercise with `Bio.PDB.MMCIFParser`
   on an `.cif` file. The output should be identical.

Next module: how protein language models tokenise and embed sequences.
