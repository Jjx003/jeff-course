## Hints

1. Backbone parsing is reused from module 8 — count CA atoms in the
   embedded PDB:

```python
def parse_backbone(pdb_str: str) -> int:
    n = 0
    for line in pdb_str.splitlines():
        if line.startswith("ATOM") and " CA " in line:
            n += 1
    return n
```

For a real ProteinMPNN run you'd extract the full backbone (N, CA,
C, O) coordinates per residue and feed them to the model. The stub
only needs the residue count to size its sampling loop.

2. The stub uses NumPy with a deterministic seed:

```python
import numpy as np

ALPHABET = "ACDEFGHIKLMNPQRSTVWY"

def stub_inverse_fold(wt_sequence, num_samples=5, seed=0,
                       temperature=1.0, wt_bias=2.0):
    samples = []
    for k in range(num_samples):
        rng = np.random.default_rng(seed + k)
        seq_chars = []
        log_prob_total = 0.0
        for wt_aa in wt_sequence:
            logits = rng.standard_normal(20) * 1.5
            wt_idx = ALPHABET.index(wt_aa)
            logits[wt_idx] += wt_bias
            scaled = logits / temperature
            probs = np.exp(scaled - scaled.max())
            probs /= probs.sum()
            chosen_idx = rng.choice(20, p=probs)
            log_prob_total += float(np.log(probs[chosen_idx]))
            seq_chars.append(ALPHABET[chosen_idx])
        samples.append(("".join(seq_chars), log_prob_total))
    return samples
```

Notes:

- We use `default_rng` for clean per-sample seeding.
- `wt_bias = 2.0` makes the WT residue's logit 2 units higher than
  the noise; this gives ~30-50 % recovery on average, which mimics
  real ProteinMPNN behaviour.
- The temperature parameter scales the logits before softmax;
  higher = more diverse, lower = more peaked.

3. Recovery:

```python
def recovery(seq: str, wt: str) -> int:
    return sum(a == b for a, b in zip(seq, wt))
```

Returns a count; format as a fraction in the print loop.

4. The "real" ProteinMPNN call (use this if you have it installed):

```python
def real_inverse_fold(pdb_path, wt_sequence, num_samples=5):
    import protein_mpnn  # the actual package after install
    # Wrap protein_mpnn_run.py's main function or use the API.
    # Returns list of (sequence, log_prob) tuples.
    raise NotImplementedError(
        "Plug your install in here. See https://github.com/dauparas/ProteinMPNN"
    )
```

The wrapper above is intentionally a stub — ProteinMPNN's API has
changed between versions, and the cleanest path is usually to call
the bundled `protein_mpnn_run.py` script as a subprocess. The
stub-based path in the starter is the recommended one for this
exercise.

5. Try / except around the import:

```python
try:
    inverse_fold = real_inverse_fold
    print("ProteinMPNN inverse folding (real model)")
except Exception as e:
    print(f"  (ProteinMPNN not available: {e})")
    inverse_fold = stub_inverse_fold
    print("ProteinMPNN inverse folding (stub fallback)")
```

In the starter we always use the stub — getting ProteinMPNN
properly wired up is a separate exercise that depends heavily on
your environment.

## Sanity checks

- The 12-residue WT sequence should have exactly 12 CA atoms in the
  embedded PDB. If `parse_backbone` returns a different number, the
  PDB string is malformed.
- All 5 sampled sequences should have the same length (12) as the
  WT.
- With `wt_bias=2.0`, recovery should average 30-50 % across
  samples. If you see 0 % across the board, your bias term has the
  wrong sign or is being overwritten.
- Total log-probability should be in the range $-1$ to $-30$ for a
  12-residue sequence at $\tau=1.0$. If you're seeing $-300$, you
  likely forgot to softmax (you're using raw logits).

## Going deeper

- **Dauparas et al, 2022** — *Robust deep learning–based protein sequence design using ProteinMPNN* — [https://www.science.org/doi/10.1126/science.add2187](https://www.science.org/doi/10.1126/science.add2187). The original ProteinMPNN paper. Includes recovery, expression, and de novo binder benchmarks.
- **Hsu et al, 2022** — *Learning inverse folding from millions of predicted structures* — [https://www.biorxiv.org/content/10.1101/2022.04.10.487779](https://www.biorxiv.org/content/10.1101/2022.04.10.487779). The ESM-IF1 paper. Argues for transformer-based inverse folding scaled with AlphaFold-augmented training data.
- **Watson et al, 2023** — *De novo design of protein structure and function with RFdiffusion* — [https://www.nature.com/articles/s41586-023-06415-8](https://www.nature.com/articles/s41586-023-06415-8). RFdiffusion for backbone *generation*; pairs with ProteinMPNN for sequence design.
- **Verkuil et al, 2022** — *Language models generalize beyond natural proteins* — [https://www.biorxiv.org/content/10.1101/2022.12.21.521521v1](https://www.biorxiv.org/content/10.1101/2022.12.21.521521v1). De novo design via ESM-IF1.
- **AlphaFold3 paper** — *Accurate structure prediction of biomolecular interactions with AlphaFold 3* — [https://www.nature.com/articles/s41586-024-07487-w](https://www.nature.com/articles/s41586-024-07487-w). AlphaFold3 includes natively inverse-folding inference.
- **ProteinMPNN repo** — [https://github.com/dauparas/ProteinMPNN](https://github.com/dauparas/ProteinMPNN). Reference implementation; the README has install + usage instructions, and `examples/` has end-to-end scripts.

## Things to try after

1. **Vary the temperature.** Re-run the stub at $\tau \in \{0.1, 0.3, 1.0, 3.0\}$. Watch recovery climb at low $\tau$ and diversity climb at high $\tau$.
2. **Real ProteinMPNN run.** Clone the repo, install, and run
   `protein_mpnn_run.py --pdb_path your.pdb --num_seq_per_target 5`.
   Compare to the stub output qualitatively.
3. **Round-trip with ESMFold.** Take ProteinMPNN's top-recovered
   sample from a real protein, fold it with ESMFold (module 18),
   and compute RMSD against the original backbone (module 19).
   Aim for RMSD < 1 Å for a good design.
4. **Mix and rank.** Score each ProteinMPNN sample with ESM-2 PLL
   (module 20). Sort candidates by `(plddt + alpha * pll)` for some
   weight $\alpha$. This is the simplest version of Cradle's
   composite scorer.
5. **Constraint masking.** Real ProteinMPNN supports per-position
   masks: "fix this residue", "design this residue freely",
   "exclude this residue". These let you redesign just the
   surface of a protein while preserving the binding pocket.

Final module — module 22 — is the capstone: how all of the above
plumbing fits into a real ML-protein-engineering pipeline (the
Cradle "logiter" loop).
