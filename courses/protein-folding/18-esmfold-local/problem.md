## Goal

Load ESMFold, fold the same 30-residue myoglobin fragment from
modules 11-12, and print:

1. Time taken to load the model (typically dominated by weight
   download and disk I/O on the first run).
2. Time taken for the forward pass (the actual folding).
3. Mean pLDDT across all residues.
4. The first ~20 lines of the predicted PDB string.

This is the simplest possible structure-prediction script — fewer
than 30 lines of code — and it produces a file you can drop into
PyMOL or RCSB's NGL viewer.

## Hardware

- **Recommended:** NVIDIA GPU with $\ge 16$ GB VRAM. ESMFold's
  default settings need ~10 GB for a 30-residue peptide and grow
  fast with sequence length.
- **Acceptable:** $\ge 8$ GB VRAM with `model.trunk.set_chunk_size(64)`,
  which trades time for memory.
- **Not recommended:** CPU. ESMFold on CPU takes >10 minutes per
  protein, often more. If you don't have a GPU, **read the code and
  move to module 19** — that one runs CPU-fast.

The HuggingFace `transformers` port of ESMFold downloads ~10-13 GB
of weights on first use (the ESM-2 3B backbone plus the structure
module — see module 17 for why the public `facebook/esmfold_v1`
ships the 3B-backbone variant rather than the 15B one from the
paper). Subsequent runs are instant — weights are cached in
`~/.cache/huggingface/`.

We use the HuggingFace port (`facebook/esmfold_v1` via
`transformers.EsmForProteinFolding`) rather than the original
`fair-esm` package because the install path is much simpler —
no openfold / nvidia-dllogger pinning headaches.

## The exercise

1. Load ESMFold:

   ```python
   import torch
   from transformers import EsmForProteinFolding

   model = EsmForProteinFolding.from_pretrained(
       "facebook/esmfold_v1",
       low_cpu_mem_usage=True,
   )
   model.eval()
   model = model.cuda()
   model.esm = model.esm.half()  # FP16 backbone for ~10 GB VRAM
   ```

   Optionally set `model.trunk.set_chunk_size(64)` to reduce the
   structure-module memory at the cost of slightly slower inference.

2. Fold the sequence:

   ```python
   sequence = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"
   with torch.no_grad():
       pdb_str = model.infer_pdb(sequence)
   ```

   `infer_pdb` returns the predicted structure already formatted as
   a PDB string. It internally tokenises the input, runs the model,
   strips the `<cls>` / `<eos>` positions from the output, and
   formats the per-atom coordinates with pLDDT in the B-factor
   column. For batched inputs use `model.infer_pdbs([s1, s2, ...])`.

3. Compute and print stats:

   - Mean pLDDT across all residues. The structure module's output
     stores it in the B-factor column of the PDB; you can parse it
     out with `Bio.PDB` (module 8) or with a quick string scan.
   - Sequence length, time taken, model parameter count.

## Expected output (illustrative)

```text
Loading ESMFold v1 ...
Model loaded in 14.21 s
Parameters: 3,041,250,272

Sequence (length 30):
MGLSDGEWQLVLNVWGKVEADIPGHGQEVL

Folding (FP16 on cuda) ...
Forward pass: 1.23 s

Result:
  Sequence length: 30
  Mean pLDDT:      78.4
  pLDDT range:     [56.3, 89.2]

First 8 lines of predicted PDB:
PARENT N/A
ATOM      1  N   MET A   1      -2.347   1.890  -0.122  1.00 64.21           N
ATOM      2  CA  MET A   1      -1.456   2.701  -0.974  1.00 64.21           C
ATOM      3  C   MET A   1      -0.038   2.140  -0.853  1.00 64.21           C
ATOM      4  O   MET A   1       0.231   1.094  -1.434  1.00 64.21           O
ATOM      5  CB  MET A   1      -1.910   2.788  -2.444  1.00 64.21           C
ATOM      6  CG  MET A   1      -1.012   3.658  -3.314  1.00 64.21           C
ATOM      7  SD  MET A   1      -1.612   3.806  -5.024  1.00 64.21           S
```

(The exact coordinates and pLDDT values vary across versions; this
gives you the shape of correct output.)

The "B-factor" column of the PDB lines (the `64.21` in the example)
holds **pLDDT** — ESMFold reuses that field for its confidence
output. Higher = more confident; the column is the same per residue.

## What you should learn

- **One forward pass** is all it takes to fold a protein. No MSA
  search, no recycling loop, no Evoformer. The architectural sketch
  in module 17 is real.
- **pLDDT is your friend.** It tells you which parts of the prediction
  to trust. A typical run on a well-folded peptide gives mean pLDDT
  in the 70-90 range; below 50 means the model has no idea.
- **Memory dominates.** The 30-residue peptide is the easy case; for
  a 200-residue protein you'll need 16 GB and chunked attention.
- **The output is a standard PDB** — you can open it directly in
  PyMOL, ChimeraX, or any web-based 3-D viewer.

## Common runtime errors

- **`OutOfMemoryError`**: lower the chunk size
  (`model.trunk.set_chunk_size(32)` or `16`), use a shorter sequence,
  or make sure you called `model.esm = model.esm.half()` after moving
  to CUDA.
- **Sequence too long**: very long sequences (> 1500 residues) blow
  up memory regardless of chunk size; ESMFold isn't the right tool
  for them. Split into domains.
- **CPU inference hanging**: this is expected — ESMFold on CPU takes
  10+ minutes. Be patient or wait until you have a GPU.

## Saving the PDB

For real use, save the PDB string to disk:

```python
with open("predicted.pdb", "w") as f:
    f.write(pdb_str)
```

Then drop `predicted.pdb` into PyMOL: `pymol predicted.pdb`. Or open
it in your browser at [https://www.rcsb.org/3d-view](https://www.rcsb.org/3d-view) (paste the file
contents into "Custom data → Upload file"). The 3-D view is the most
satisfying part of this whole module.
