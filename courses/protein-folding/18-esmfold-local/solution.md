## Walkthrough

### Loading

```python
model = EsmForProteinFolding.from_pretrained(
    "facebook/esmfold_v1",
    low_cpu_mem_usage=True,
)
model.eval()
model = model.cuda()
model.esm = model.esm.half()
```

`EsmForProteinFolding` bundles ESM-2 (the `model.esm` attribute) +
ESMFold's structure module trunk (`model.trunk`) + the all-atom
decoder into a single `nn.Module`. The first
`from_pretrained("facebook/esmfold_v1")` call downloads ~10-13 GB
of weights to `~/.cache/huggingface/`.

`low_cpu_mem_usage=True` streams the weights through `accelerate`
(an indirect dependency) instead of allocating the full FP32 model
on the CPU before transfer.

`model.eval()` is non-trivial here because ESMFold has dropout
layers in the structure module. Skipping `.eval()` would inject
randomness into the prediction.

Half-precision the **backbone only** — leave the structure module
in FP32 because its IPA layers can lose stability under FP16. This
is the recommended pattern from the HuggingFace ESMFold docs.

### Memory safeguard

```python
if torch.cuda.mem_get_info()[0] < 12 * 1024 ** 3:
    model.trunk.set_chunk_size(64)
```

`mem_get_info()` returns `(free, total)` in bytes. The threshold of
12 GB is somewhat arbitrary; in practice 10 GB is enough for a
30-residue peptide without chunking, but the safety margin guards
against weight loading + temporary tensor allocation pushing
ephemerally over the limit.

`chunk_size=64` is a sweet spot for 16 GB cards: noticeable memory
reduction with only a small speed hit. For 8 GB cards drop it to 32
or 16; for 24 GB+ cards skip it entirely.

### Folding

```python
with torch.no_grad():
    pdb_str = model.infer_pdb(SEQUENCE)
```

`infer_pdb` is the highest-level API — input string in, PDB string
out. Internally it does:

1. Tokenise the sequence with ESM-2's alphabet (no need to call a
   tokenizer yourself).
2. Run the ESM-2 backbone to produce per-residue embeddings.
3. Run the structure module to produce per-atom coordinates and
   pLDDT scores.
4. Strip the `<cls>` / `<eos>` positions so the output matches the
   input sequence length.
5. Format the output as a PDB string with pLDDT in the B-factor
   column.

If you want intermediate access (e.g. to the PAE matrix), use
`model.infer(SEQUENCE)` which returns a dict with keys like
`positions`, `plddt`, and `predicted_aligned_error`. The
lower-level alternative is to tokenise manually:

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
input_ids = tokenizer([SEQUENCE], return_tensors="pt", add_special_tokens=False)["input_ids"].cuda()
with torch.no_grad():
    output = model(input_ids)
pdb_str = model.output_to_pdb(output)[0]
```

The `add_special_tokens=False` is essential — if you let the
tokenizer add `<cls>` / `<eos>` you need to manually drop their
positions from `output.positions` before calling `output_to_pdb`,
otherwise the PDB picks up two phantom residues at the ends.

### Parsing pLDDT

```python
for line in pdb_str.splitlines():
    if line.startswith("ATOM"):
        plddt = float(line[60:66].strip())
        resi = int(line[22:26].strip())
        if resi not in seen:
            plddts.append(plddt)
            seen.add(resi)
```

We exploit the column-positional nature of PDB ATOM lines:

- Cols 23-26 (Python slice `[22:26]`) — residue sequence number.
- Cols 61-66 (Python slice `[60:66]`) — B-factor (= pLDDT here).

The `seen` set deduplicates: every residue has multiple atoms but
the same pLDDT, so we only record once per residue.

A more robust alternative is to use Biopython's `PDBParser` (module
8) and read `atom.bfactor`. The string-parsing version is shorter
and avoids the dependency, but `Bio.PDB` is the production-quality
approach.

### Why this whole pipeline is a few-line script

Most of the code in `solution/python.py` is bookkeeping —
device-handling, timing, formatting. The actual *folding* is one
line:

```python
pdb_str = model.infer_pdb(SEQUENCE)
```

This is the take-away from module 17 made concrete: ESMFold is a
single forward pass. Everything else is plumbing.

## Reading the result

For our globin fragment, expect:

- **Mean pLDDT**: ~70-80. The fragment is part of a well-known fold
  (the globin family), so the model has lots of training-set context
  and produces a confident prediction.
- **pLDDT range**: minimum is usually at the N-terminus or
  C-terminus (terminals are intrinsically less constrained); maximum
  is in the middle of helix segments.
- **Forward pass time**: 1-5 seconds on a typical GPU. Includes the
  full ESM-2 backbone + structure module.

## What the predicted PDB should look like

A well-folded prediction for `MGLSDGEWQLVLNVWGKVEADIPGHGQEVL` is
mostly an alpha-helix. In a structure viewer:

- A single dominant helix from residue 4 to ~25.
- Loose coil at the N- and C-termini.
- Standard right-handed helical pitch (3.6 residues per turn).
- The conserved `WGK` motif (residues 15-17) sits at the start of
  the E-helix in real globin structures; in our fragment it lives
  near the end of the N-terminal helix instead.

If the prediction *isn't* mostly helical, something is off — likely
a sequence error or a model failure on a particularly hard input.

## Why this output isn't graded byte-exactly

Three sources of run-to-run variation:

1. **FP16 inference** is non-deterministic across hardware (different
   GPUs, different CUDA / cuDNN versions can give slightly different
   floating-point answers).
2. **`transformers` ESMFold versions** occasionally update the
   structure module wrappers between releases.
3. **`set_chunk_size`** can introduce tiny numerical differences in
   the attention computation depending on chunk boundaries.

The qualitative shape — a confidently folded helix — is robust
across all these. Numbers vary at the 3rd-decimal level.

## Going beyond this module

For real applications:

- **Save the PDB** to disk and view it in PyMOL or NGL viewer.
- **Compute confidence-weighted ensemble averages** if you fold
  multiple variants of a sequence.
- **Pair with a quality filter** in production — drop predictions
  with mean pLDDT < 70 before downstream tasks.
- **Try AlphaFold3 / ColabFold** on the same input for comparison.
  ESMFold is fast; AlphaFold-family methods are accurate. Use the
  right tool for your budget.

Next module — module 19 — quantifies "how close are two structures"
with RMSD and a TM-score-like metric. That's the language you'd use
to compare ESMFold's output against an experimental structure.
