## Hints

1. Loading ESMFold (HuggingFace transformers port):

```python
import time
import torch
from transformers import EsmForProteinFolding

t0 = time.perf_counter()
model = EsmForProteinFolding.from_pretrained(
    "facebook/esmfold_v1",
    low_cpu_mem_usage=True,
)
model.eval()
device = "cuda" if torch.cuda.is_available() else "cpu"
if device == "cuda":
    model = model.cuda()
    model.esm = model.esm.half()  # half-precision the backbone
    torch.backends.cuda.matmul.allow_tf32 = True
load_time = time.perf_counter() - t0
```

The first load downloads ~10-13 GB of weights from the HuggingFace
hub. Be patient; it's a one-time cost cached under
`~/.cache/huggingface/`.

2. Memory protection — for safety on consumer GPUs:

```python
if device == "cuda":
    free_gb = torch.cuda.mem_get_info()[0] / 1024 ** 3
    if free_gb < 12:
        print(f"  Setting chunk_size=64 (only {free_gb:.1f} GB free)")
        model.trunk.set_chunk_size(64)
```

3. Fold:

```python
SEQUENCE = "MGLSDGEWQLVLNVWGKVEADIPGHGQEVL"
t0 = time.perf_counter()
with torch.no_grad():
    pdb_str = model.infer_pdb(SEQUENCE)
if device == "cuda":
    torch.cuda.synchronize()
fold_time = time.perf_counter() - t0
```

4. Mean pLDDT (parsed from the B-factor column):

```python
plddts = []
seen_residues = set()
for line in pdb_str.splitlines():
    if line.startswith("ATOM"):
        # B-factor field is at columns 60-66 (1-indexed)
        plddt = float(line[60:66].strip())
        resi = int(line[22:26].strip())
        if resi not in seen_residues:
            plddts.append(plddt)
            seen_residues.add(resi)
mean_plddt = sum(plddts) / len(plddts)
plddt_min = min(plddts)
plddt_max = max(plddts)
```

The `seen_residues` set ensures we count each residue once (every
residue has multiple atoms but the same pLDDT).

5. Print the first 8 lines of the PDB:

```python
print("First 8 lines of predicted PDB:")
for line in pdb_str.splitlines()[:8]:
    print(line)
```

## CPU fallback

ESMFold on CPU takes 10-30 minutes for the 30-residue peptide. If
you must run CPU, *don't* half-precision the backbone — keep it in
FP32:

```python
model = EsmForProteinFolding.from_pretrained(
    "facebook/esmfold_v1",
    low_cpu_mem_usage=True,
)
model.eval()
# (no .cuda(), no .half())
```

Or just skip the exercise and proceed to module 19 — its content is
the structure-quality metrics that this module's output would feed
into.

## Sanity checks

- `pdb_str` should start with `PARENT N/A` (a header line ESMFold
  emits) followed by `ATOM` records.
- The number of `ATOM` lines should be roughly $7-8 \times L$ for
  an all-atom prediction (each residue has its backbone + side-chain
  heavy atoms).
- Mean pLDDT for a well-conserved 30-residue globin fragment should
  be in the 65-85 range. If it's below 50, something is off (wrong
  sequence, wrong model, or memory was so tight the model gave up).
- Forward pass time on a 16 GB GPU with no chunking: ~1-3 seconds.
  With `chunk_size=64`: ~3-6 seconds. With `chunk_size=16`: ~10-20
  seconds.

## Going deeper

- **Lin et al, 2023** — *Evolutionary-scale prediction of atomic-level protein structure* — [https://www.science.org/doi/10.1126/science.ade2574](https://www.science.org/doi/10.1126/science.ade2574). The ESMFold paper. Section 4 covers the structure module architecture and pLDDT calibration.
- **HuggingFace `facebook/esmfold_v1`** — [https://huggingface.co/facebook/esmfold_v1](https://huggingface.co/facebook/esmfold_v1). Model card with example code, weights, and the underlying `EsmForProteinFolding` API reference.
- **HuggingFace ESMFold blog post** — [https://huggingface.co/blog/deep-learning-with-proteins](https://huggingface.co/blog/deep-learning-with-proteins). Walkthrough of running ESMFold + ESM-2 from the `transformers` library.
- **`fair-esm` ESMFold examples** — [https://github.com/facebookresearch/esm/tree/main/scripts/esmfold](https://github.com/facebookresearch/esm/tree/main/scripts/esmfold). Original FAIR scripts for batch inference, multi-chain folding, and confidence analysis. (`fair-esm[esmfold]` install requires openfold and can be fragile; the HF port above is easier in most environments.)
- **PyMOL** — [https://pymol.org/](https://pymol.org/). The standard structure visualisation tool. Free for non-commercial use.
- **NGL viewer** — [http://nglviewer.org/](http://nglviewer.org/). Browser-based 3-D structure viewer; handles ESMFold PDBs directly.
- **Mariani et al, 2013** — *lDDT: a local superposition-free score for comparing protein structures and models using distance difference tests* — [https://academic.oup.com/bioinformatics/article/29/21/2722/195896](https://academic.oup.com/bioinformatics/article/29/21/2722/195896). The original lDDT paper that pLDDT predicts.

## Things to try after

1. **Save the PDB and visualise.** Open it in PyMOL or NGL viewer.
   Notice the helical structure of the globin N-terminal fragment.
   Colour by B-factor (= pLDDT) to see where the model is confident.
2. **Try the HBB fragment** from module 12. Compare the predicted
   structure to the MB fragment — both should fold into similar
   helices.
3. **Try a longer sequence.** Take the full 154-residue myoglobin
   from module 5 and see how memory and time scale. You'll likely
   need `chunk_size=64` or `32`.
4. **Compare with a real PDB.** Download the experimental myoglobin
   structure (PDB id `1MBN`), align with ESMFold's prediction (e.g.
   in PyMOL: `align prediction, 1mbn`), and report the RMSD.
   Should be 1-2 Å for a confident prediction.

Next module: structure quality metrics — RMSD, TM-score, lDDT — to
quantify how close two predicted/experimental structures are.
