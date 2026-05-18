## ESMFold's structure module: a tour

ESMFold's structure module is a slimmed-down AlphaFold2 structure
module. It takes:

- Per-residue ESM-2 embeddings: $\mathbf{s} \in \mathbb{R}^{L \times d}$ (with $d = 5120$ for 15B).
- A pair representation built from the embeddings:
  $\mathbf{z}_{ij} = \text{LinearProj}(\mathbf{s}_i, \mathbf{s}_j)$ —
  typically a learned outer-product-like projection.

And applies $\sim$8 layers of Invariant Point Attention (IPA),
interleaved with backbone-frame updates. The output is a per-residue
$(\mathbf{R}_i, \mathbf{t}_i) \in SE(3)$ frame plus side-chain torsion
angles, which together specify all atom positions.

### Invariant Point Attention, in one paragraph

IPA is attention with a geometric twist. In addition to the usual
QKV projections, each position emits a small set of **3-D query
points** and **3-D key points** in its local backbone frame. The
attention scores include a term proportional to the *distance*
between mapped query and key points after applying the residue-frame
transformations.

The result: attention is **SE(3)-invariant** — translating or
rotating the whole protein doesn't change the attention weights.
This is critical for correctly handling 3-D structure, which has no
preferred coordinate origin.

The math involves Lie groups and is a digression from this course's
main thread; we won't unpack it. The high-level point is: ESMFold
inherits this IPA mechanism from AlphaFold2 with minor modifications.

## pLDDT: ESMFold's confidence score

ESMFold (and AlphaFold2 / 3) produces a per-residue confidence score
called **pLDDT** (predicted Local Distance Difference Test). Range
0-100; higher is better. Roughly:

- $> 90$: very high confidence, essentially experimental quality.
- $70-90$: confident, good for most uses.
- $50-70$: low confidence, treat the local geometry with skepticism.
- $< 50$: very low confidence, often disordered or unpredictable.

Module 19 uses pLDDT and related metrics in the structure-quality
exercise.

A clever feature of ESMFold's training: pLDDT is predicted *jointly*
with the structure, so it's calibrated against the model's own error
distribution. If ESMFold says pLDDT 75, it really means the
prediction is at the level a 75-pLDDT prediction is supposed to be.

## When ESMFold goes wrong

Failure modes I've seen in the wild:

- **Disordered regions** are predicted with very low pLDDT (often
  $< 30$). This is *correct* — they don't have a single structure —
  but the predicted coordinates for these regions are essentially
  noise. Don't trust them.
- **Long flexible loops** are sometimes "frozen" into one
  conformation in the prediction even though the real protein has
  many. pLDDT helps flag these.
- **Membrane proteins** generally fold worse than soluble globular
  proteins, partly because UniRef50 over-represents soluble proteins
  and partly because membrane geometry is harder.
- **Antibody CDR loops** in early lineages (immature antibodies) can
  be wrong because the model has poor coverage of pre-affinity-matured
  variable regions.
- **Coiled-coils** can be predicted as straight helices with the
  wrong dimerisation geometry. AlphaFold-Multimer does better on
  multi-chain coiled-coils.

For each failure mode, the fix is usually "use a more specialised
tool" — RFdiffusion for de novo design, AlphaFold-Multimer for
multimeric assemblies, etc.

## Speed in practice

Wall-clock time on an A100 GPU for ESMFold:

- 30-residue peptide: $\sim 1$ second (mostly model loading the first
  time).
- 100-residue: $\sim 2$ seconds.
- 300-residue: $\sim 5$ seconds.
- 1000-residue: $\sim 30-60$ seconds + chunked attention.
- 2000-residue: needs chunking + might OOM on 24 GB cards.

AlphaFold2 on the same hardware:

- 30 residues: ~5 minutes (mostly MSA search).
- 100 residues: ~10 minutes.
- 300 residues: ~30 minutes.

ESMFold's win on throughput is enormous — you can predict tens of
thousands of structures per day on a single GPU.

## ColabFold: the practical hybrid

In practice, most people don't run "vanilla" AlphaFold2 — they run
**ColabFold** ([https://colab.research.google.com/github/sokrypton/ColabFold](https://colab.research.google.com/github/sokrypton/ColabFold)), which uses MMseqs2 (much faster than HHblits) for MSA search
and the AlphaFold2 model itself for structure prediction. ColabFold
is typically 5-10× faster than vanilla AlphaFold2.

ESMFold is still much faster than ColabFold (no MSA search at all),
but for production workflows where MSAs are useful anyway (e.g.
multi-chain prediction), ColabFold remains a solid choice.

## What about AlphaFold3?

AlphaFold3 (released 2024) takes a different architectural turn:

- **Diffusion-based structure module** rather than IPA.
- **Joint prediction** of proteins, ligands, nucleic acids, modified
  residues, and PTMs.
- Still uses MSAs but with a different MSA-encoding scheme.

Compared to ESMFold:

- AlphaFold3 is **slower** than ESMFold but **handles more types of
  inputs**.
- AlphaFold3 is **more accurate** on average but **needs the MSA
  pipeline**.

For pure protein-only single-chain structure prediction in 2024-2025,
the choice between ESMFold and AlphaFold3 is mostly about throughput
vs accuracy. For multi-component complexes, AlphaFold3 is the
relevant option.

## ESMFold and the compressed-database view

Rerunning module 10's framing through the ESMFold lens:

- **The compressed database** is now ESM-2 15B's full set of
  parameters (~30 GB in FP16).
- **The query** is a single sequence — no MSA needed.
- **The retrieved match** is the per-residue embedding tensor, which
  encodes structural / co-evolutionary context implicitly.
- **The decoder** is the structure module, which reads coordinates
  out of the implicit representation.

Notice the parallel to module 14's ESM3 pipeline: ESMFold is a
specialised inverse of ESM3's "sequence → structure" path, where the
structure tokens have been replaced by direct coordinate prediction.

## Choosing between ESM-2, ESMFold, AlphaFold2, AlphaFold3

A pragmatic decision tree for "should I fold this protein":

1. **Have a deep MSA and need maximum accuracy?** ColabFold (≈AlphaFold2)
   or AlphaFold3.
2. **Need to fold many proteins fast?** ESMFold.
3. **Have a single, MSA-poor or orphan protein?** ESMFold.
4. **Need to fold a multimer or complex with ligands?** AlphaFold3
   or AlphaFold-Multimer.
5. **Just need per-residue embeddings (not coordinates)?** ESM-2
   alone, no structure module.

Module 18 walks through option 2 in code.

## The historical irony

The 2010s consensus was: "deep MSAs are necessary for accurate
structure prediction; without them you can't fold proteins". DCA,
EVfold, and the early CASP results all required thousands of
homologous sequences.

ESMFold inverts this: scale a generic language model enough, and the
model's parameters carry the same signal a thousand-sequence MSA
would. The MSA at inference time becomes a *redundant data
representation* of what the model already knows.

This is a recurring theme in ML: explicit data structures get
compressed into model weights when the model is large enough. We've
seen the same arc with explicit knowledge graphs (compressed into
LLMs) and explicit retrieval databases (sometimes compressed,
sometimes still useful as RAG).

For proteins, the compression is *just* good enough at 15B parameters
to dethrone the explicit MSA pipeline for most practical use cases —
but not so absolute that the explicit pipeline becomes irrelevant.
The two systems are likely to coexist for years.
