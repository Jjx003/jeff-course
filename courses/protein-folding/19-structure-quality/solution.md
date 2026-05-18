## Walkthrough

### Coordinate extraction

```python
def ca_coords(pdb_str: str) -> np.ndarray:
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("s", StringIO(pdb_str))
    ca = [res["CA"] for res in structure[0]["A"]
          if res.id[0] == " " and "CA" in res]
    return np.array([atom.coord for atom in ca])
```

Same idiom as module 8: walk the chain, filter for standard residues
with a CA atom, stack into a NumPy array. The returned shape is
`(N, 3)` where N is the number of CA atoms.

### RMSD

```python
def rmsd_and_distances(p, q):
    diffs = p - q
    distances = np.linalg.norm(diffs, axis=1)
    rms = float(np.sqrt(np.mean(distances ** 2)))
    return rms, distances
```

Three-line RMSD. The `axis=1` in `np.linalg.norm` reduces over the 3-vector dimension, leaving a length-N distance vector. We square,
mean, and sqrt to get RMSD.

For our toy: distances = $[0, 0, 1, 1, 0]$, mean of squares = $0.4$,
RMSD = $\sqrt{0.4} \approx 0.6325$.

### TM-score-like

```python
def tm_like(distances, d0):
    return float(np.mean(1.0 / (1.0 + (distances / d0) ** 2)))
```

The formula

$$S = \frac{1}{L}\sum_{i=1}^{L} \frac{1}{1 + (d_i/d_0)^2}$$

becomes a one-line vectorised expression. NumPy broadcasts the
scalar `d0` over the distance vector.

For our toy with $d_0 = 2.0$: each term is either $1$ (when $d_i = 0$)
or $1 / (1 + 0.25) = 0.8$ (when $d_i = 1$). Mean = $(1 + 1 + 0.8 + 0.8 + 1) / 5 = 0.92$.

### pLDDT extraction

```python
def plddt_per_residue(pdb_str):
    plddts = []
    seen = set()
    for line in pdb_str.splitlines():
        if not line.startswith("ATOM"):
            continue
        bfac = float(line[60:66].strip())
        resi = int(line[22:26].strip())
        if resi not in seen:
            plddts.append(bfac)
            seen.add(resi)
    return plddts
```

We exploit PDB's positional column layout:

- Cols 23-26 (Python slice `[22:26]`): residue number.
- Cols 61-66 (Python slice `[60:66]`): B-factor (= pLDDT in
  AlphaFold / ESMFold output).

The `seen` set deduplicates: every residue has many atoms, but they
all share the same pLDDT, so we only record once per residue.

A more "correct" approach would be to use Biopython's `PDBParser`
and read `atom.bfactor`, but for a one-off script the string
parsing is shorter and avoids a dependency on the Bio.PDB API for
this specific column.

## Verifying the numbers

### RMSD

Per-residue distances:

- $d_1 = \lVert (0, 0, 0) - (0, 0, 0) \rVert = 0$
- $d_2 = 0$
- $d_3 = \lVert (7.6, 0, 1) - (7.6, 0, 0) \rVert = 1$
- $d_4 = 1$
- $d_5 = 0$

$\text{RMSD} = \sqrt{(0 + 0 + 1 + 1 + 0)/5} = \sqrt{0.4} \approx 0.63246$.

Rounded to 4 decimals: $0.6325$.

### TM-like

With $d_0 = 2.0$ and the same distances:

| $i$ | $d_i$ | $(d_i/d_0)^2$ | $1/(1 + \cdot)$ |
|---|---|---|---|
| 1 | 0 | 0 | 1.0 |
| 2 | 0 | 0 | 1.0 |
| 3 | 1 | 0.25 | $1/1.25 = 0.8$ |
| 4 | 1 | 0.25 | 0.8 |
| 5 | 0 | 0 | 1.0 |

Mean: $(1 + 1 + 0.8 + 0.8 + 1)/5 = 4.6/5 = 0.92$.

### pLDDT

Sum: $88 + 75 + 62 + 92 + 81 = 398$. Mean: $79.6$.

Counts above thresholds:

- $> 70$: $\{88, 75, 92, 81\}$, four residues; fraction $4/5 = 0.80$.
- $> 90$: $\{92\}$, one residue; fraction $1/5 = 0.20$.

## Floating-point note

`np.sqrt(0.4)` should round identically across PyTorch, NumPy, and
plain Python `math.sqrt` to the same FP double. Printed with
`.4f`, the result is `"0.6325"` regardless. Same for the
TM-like calculation: $4.6 / 5$ is not exactly representable in FP
but rounds to `"0.9200"` reliably.

## Connection to the rest of the course

These three metrics are the standard tools for evaluating any
structure prediction:

- **RMSD** is your default first-pass quality score.
- **TM-score** lets you compare across proteins of different sizes,
  and is the headline number in most prediction papers.
- **pLDDT** is the model's self-reported confidence; use it to
  filter or weight predictions in downstream pipelines (e.g. the
  Cradle pipeline in module 22 keeps only high-pLDDT regions for
  evotuning).

A real pipeline runs ESMFold (module 18), parses pLDDT per residue,
filters to the confident core, then evaluates against an
experimental reference using TM-score. Module 22 ties this
evaluation step into a full lead-optimisation loop.
