## Hints

1. Parse two PDBs and extract CA coordinates as in module 8:

```python
from io import StringIO
from Bio.PDB import PDBParser
import numpy as np

def ca_coords(pdb_str: str) -> np.ndarray:
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("s", StringIO(pdb_str))
    ca = [res["CA"] for res in structure[0]["A"]
          if res.id[0] == " " and "CA" in res]
    return np.array([atom.coord for atom in ca])
```

2. RMSD without alignment:

```python
def rmsd(p: np.ndarray, q: np.ndarray) -> tuple[float, np.ndarray]:
    diffs = p - q
    distances = np.linalg.norm(diffs, axis=1)
    rms = float(np.sqrt(np.mean(distances ** 2)))
    return rms, distances
```

3. The TM-score-like metric:

```python
def tm_like(distances: np.ndarray, d0: float) -> float:
    return float(np.mean(1.0 / (1.0 + (distances / d0) ** 2)))
```

4. pLDDT extraction (B-factor column of ATOM lines):

```python
def plddt_per_residue(pdb_str: str) -> list[float]:
    plddts = []
    seen = set()
    for line in pdb_str.splitlines():
        if line.startswith("ATOM"):
            try:
                bfac = float(line[60:66].strip())
                resi = int(line[22:26].strip())
            except ValueError:
                continue
            if resi not in seen:
                plddts.append(bfac)
                seen.add(resi)
    return plddts
```

5. Output format: format distance lists with `f"{x:.3f}"` and join
   with `", "`.

```python
def fmt_distances(d: np.ndarray) -> str:
    return "[" + ", ".join(f"{x:.3f}" for x in d) + "]"
```

The expected output uses these specific formats:
- Distances and RMSD: `.3f` and `.4f` respectively (note: `.4f` for
  RMSD).
- TM-like and $d_0$: `.4f` and `.3f`.
- Mean / min / max pLDDT: `.2f`.
- Fractions: `.2f` followed by `(numerator/denominator)`.

## Sanity checks

- The two PDBs you parse should give exactly 5 CA atoms each. If
  you get a different number, you've mis-pasted one of the embedded
  strings.
- Per-residue distances should be `[0.0, 0.0, 1.0, 1.0, 0.0]`.
- RMSD = $\sqrt{0.4} \approx 0.6325$. If you get $0.7071 = \sqrt{0.5}$, you forgot to divide by $N$.
- TM-like score = 0.92. If you get something dramatically different,
  check that you're computing $d_i / d_0$ before squaring.
- The pLDDT list should be `[88.0, 75.0, 62.0, 92.0, 81.0]`. If
  you get all `0.0`, the B-factor column is being parsed from the
  wrong field.

## Going deeper

- **Kabsch, 1976** — *A solution for the best rotation to relate two sets of vectors* — the original Kabsch alignment paper. Surprisingly readable; one page.
- **Zhang & Skolnick, 2004** — *Scoring function for automated assessment of protein structure template quality* — [https://onlinelibrary.wiley.com/doi/10.1002/prot.20264](https://onlinelibrary.wiley.com/doi/10.1002/prot.20264). The original TM-score paper. Includes the $d_0(L)$ derivation.
- **Mariani et al, 2013** — *lDDT: a local superposition-free score for comparing protein structures and models using distance difference tests* — [https://academic.oup.com/bioinformatics/article/29/21/2722/195896](https://academic.oup.com/bioinformatics/article/29/21/2722/195896). The lDDT paper.
- **Zemla et al, 1999** — *Processing and analysis of CASP3 protein structure predictions* — [https://www.sciencedirect.com/science/article/abs/pii/S0907444999003480](https://www.sciencedirect.com/science/article/abs/pii/S0907444999003480). The original GDT_TS paper.
- **TM-align tool** — [https://zhanggroup.org/TM-align/](https://zhanggroup.org/TM-align/). Reference C++ implementation; the Python wrapper `tmtools` is a thin binding.
- **OpenStructure / lDDT online server** — [https://swissmodel.expasy.org/lddt/](https://swissmodel.expasy.org/lddt/). Browser-based lDDT computation; useful sanity check.

## Things to try after

1. **Implement Kabsch alignment.** Add a step that translates and
   rotates `pred_coords` to minimise RMSD against `true_coords`,
   then re-compute. For our symmetric toy the improvement is small;
   try a non-symmetric perturbation and see Kabsch shine.
2. **Vary $d_0$.** Compute the TM-like metric for $d_0 \in \{0.5, 1, 2, 5, 10\}$ Å. Plot how the score changes with $d_0$. The
   shape is the "sensitivity curve" — small $d_0$ is harsh, large
   $d_0$ is forgiving.
3. **Use the real TM-score formula.** For a 50-residue protein,
   compute $d_0(50) = 1.24 \cdot 35^{1/3} - 1.8 \approx 1.34$. Re-run
   the metric on a real prediction and compare to a published
   TM-score from `tmtools`.
4. **Hinge-bend test.** Build a "two-domain" toy where one domain is
   rotated relative to the other. Compute RMSD before and after
   Kabsch — RMSD will be high (the domains can't both align). Then
   compute lDDT (or our TM-like with small $d_0$ on per-domain
   slices). The local metric will be much higher because it doesn't
   need a global superposition.

Next module: ESM-2 pseudo-log-likelihood as a zero-shot variant
effect predictor.
