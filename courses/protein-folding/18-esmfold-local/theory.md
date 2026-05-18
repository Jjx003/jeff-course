## What `infer_pdb` actually does

The convenience function hides four steps:

1. **Tokenise** the sequence with the ESM-2 alphabet (the same one
   we used in module 11) — automatically.
2. **Run the ESM-2 backbone + structure module** to produce per-atom
   coordinates, pLDDT scores, and PAE (predicted aligned error).
3. **Strip the `<cls>` / `<eos>` positions** from the output so the
   PDB matches the input sequence length exactly. (If you ever
   roll your own forward pass, you need to do this trimming
   manually before assembling the PDB lines.)
4. **Format as PDB** — assemble standard `ATOM` lines with the
   correct atom names, residue names, and pLDDT in the B-factor
   column.

If you want the raw outputs (per-atom tensor + pLDDT array + PAE
matrix), use `model.infer(sequence)` instead, which returns a dict
with keys like `positions`, `plddt`, and `predicted_aligned_error`.

## Memory and the chunk-size knob

ESMFold's main memory consumer is **attention**, which scales as
$O(L^2)$ in sequence length. For a 30-residue peptide this is fine; for
a 1000-residue protein, the $1000^2 = 10^6$ entries of the attention
matrix per layer per head, multiplied by 36 layers and 40 heads
(for the 3B ESM-2 backbone used by `facebook/esmfold_v1`),
adds up.

`model.trunk.set_chunk_size(N)` processes the structure-module
attention matrix in chunks of $N$ rows at a time. Memory drops to
$O(LN)$; time grows to $O(L^2/N)$ per layer. Common settings:

- No chunking (`None`): fastest, biggest memory.
- `chunk_size=128`: typical for medium proteins on 24 GB cards.
- `chunk_size=64`: for 16 GB cards.
- `chunk_size=16`: extreme memory pressure, very slow.

For a 30-residue peptide, no chunking is fine. For sequences > 500
residues on consumer GPUs, chunking is mandatory. Also remember to
half-precision the ESM-2 backbone: `model.esm = model.esm.half()`
after `.cuda()`, which cuts ESM-2's footprint roughly in half.

## pLDDT, the per-residue confidence

ESMFold trains a small head to predict the **per-residue Local
Distance Difference Test** (lDDT) score. The lDDT score itself is a
classical structural-similarity metric (Mariani et al, 2013):

$$\text{lDDT}_i = \text{average}\!\left[ \mathbb{1}\!\left[ |D_{ij}^{\text{pred}} - D_{ij}^{\text{ref}}| < \tau \right] \right]_{j: D_{ij}^{\text{ref}} < R}$$

where the average is over neighbours $j$ within a reference radius
$R$ (typically 15 Å), $\tau$ is a tolerance threshold (typically 0.5,
1, 2, 4 Å — averaged), and the indicator counts how many distances
are within tolerance. lDDT is bounded in $[0, 1]$; ESMFold outputs it
scaled to $[0, 100]$.

**Predicted lDDT (pLDDT)** is ESMFold's estimate of what lDDT *would*
be if the prediction were compared to the (unknown) ground truth.
The model is trained to predict pLDDT alongside the structure, so the
score is calibrated against its own error distribution.

Interpretation:

- $> 90$: very high confidence. The model trusts itself; you can trust
  it too.
- $70-90$: confident. Local geometry is reliable.
- $50-70$: low confidence. Backbone trace is roughly right, side
  chains and exact positions less so.
- $< 50$: very low confidence. The model is essentially saying "I
  don't know." Often disordered or unique-fold regions.

## The PDB B-factor convention

In a real X-ray crystal structure, the B-factor (column 61-66 of an
ATOM line) measures atomic displacement — how "fuzzy" the electron
density is for that atom. Real B-factors range from ~5 (very ordered,
buried atoms) to ~50+ (disordered surface atoms).

Both AlphaFold2 and ESMFold **repurpose** the B-factor column to
store pLDDT. This is convenient:

- Standard structural-visualisation software (PyMOL, ChimeraX, NGL
  viewer) supports B-factor colouring out of the box. Loading an
  ESMFold PDB and "color by B-factor" gives you a confidence
  heatmap for free.
- The data is per-atom but ESMFold writes the same pLDDT value for
  every atom of a residue.

The downside: you can't use ESMFold-predicted PDBs in any pipeline
that expects "real" B-factors (e.g. crystallographic refinement
tools). Always make sure downstream tools know what's in the column.

## PAE: predicted aligned error

Beyond pLDDT, ESMFold produces a **PAE** (Predicted Aligned Error)
matrix of shape $(L, L)$. PAE$_{ij}$ is the predicted error in the
position of residue $j$ when aligned on residue $i$'s frame. Units are
Ångströms; lower is better.

PAE is what you check when assessing **inter-domain confidence**: if
the PAE between domains is $> 15$ Å, the relative orientation of those
domains is unreliable even if individual pLDDTs are high. For
single-domain proteins, PAE is mostly redundant with pLDDT.

This module only prints pLDDT for simplicity, but `model.infer(...)`
returns the PAE matrix too.

## How long can ESMFold fold?

In theory: any sequence. In practice, memory and time grow fast:

| Length (residues) | VRAM (FP16) | Time (A100) |
|---|---|---|
| 30 | ~3 GB | ~1 s |
| 100 | ~4 GB | ~2 s |
| 300 | ~8 GB | ~5 s |
| 500 | ~12 GB | ~10 s |
| 1000 | ~24 GB (chunked) | ~60 s |
| 2000 | $\ge$ 40 GB | several minutes |

For protein chains > ~1500 residues you're typically better off
splitting at known domain boundaries and folding each piece
separately, then assembling the parts. AlphaFold-Multimer / AlphaFold3
handle long multi-domain proteins natively but have their own
constraints.

## Comparison with AlphaFold2 / ColabFold

If you want to verify ESMFold's output against a "gold standard":

```bash
# ColabFold (in a Colab notebook with a GPU)
!pip install colabfold-batch
colabfold_batch input.fasta output_dir/
```

The output structure files are also PDB-format with pLDDT in the
B-factor column. You can directly compare ESMFold and ColabFold
predictions for the same sequence.

For a well-conserved protein like myoglobin, the two predictions
agree closely — sub-1 Å RMSD, comparable pLDDT distributions.
Differences appear in flexible loops and side-chain rotamers.

## Going further

For production use:

- **Save outputs.** Write the PDB string to disk; persist the pLDDT
  array as a JSON or numpy file alongside it.
- **Batch.** `model.infer_pdbs([seq1, seq2, ...])` is more
  efficient than one-by-one calls, up to GPU memory.
- **Use the residue-level outputs.** `model.infer(...)` returns
  detailed atom positions and confidences; useful for downstream
  tasks that need finer-grained data than the PDB format provides.
- **Pair with a quality filter.** Drop predictions with mean pLDDT
  $< 70$ before downstream use; they're often unreliable.
