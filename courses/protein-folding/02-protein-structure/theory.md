## Backbone angles: φ, ψ, ω

The protein backbone has three rotatable bonds per residue:

- **φ (phi)** — rotation around the `N–Cα` bond.
- **ψ (psi)** — rotation around the `Cα–C` bond.
- **ω (omega)** — rotation around the `C–N` (peptide) bond.

Of these, $\omega$ is almost always locked at $180°$ (the peptide bond is
planar and rigid). So really every residue contributes just two free
rotational angles, $(\varphi, \psi)$.

This is the foundation of the **Ramachandran plot**: a 2D scatter of
$(\varphi, \psi)$ for every residue in a protein. Almost all points cluster
into three regions:

- $\alpha$-helix region (lower-left).
- $\beta$-sheet region (upper-left).
- Left-handed helix region (small, upper-right — mostly glycines).

The vast empty regions correspond to angle combinations that cause steric
clashes between atoms. The fact that a protein's residues all live in these
narrow allowed zones is the structural reason secondary structure is so
limited in variety. Two angles per residue × $L$ residues = $2L$ degrees of
freedom for the backbone, which is *much* smaller than the apparent
combinatorial explosion suggests.

## Why is folding fast at all? (Levinthal's paradox)

If a 100-residue protein had ten possible conformations per residue, it
would have $10^{100}$ total conformations. Even at $10^{13}$ samples per
second, exhaustively searching that space would take longer than the age of
the universe. Yet a typical protein folds in milliseconds.

This is **Levinthal's paradox** (1968). The resolution is that protein
folding is *not* a random search — it's biased by the **folding funnel**,
where partially-correct intermediates are energetically favoured over fully
random configurations. The chain finds its native fold by progressively
locking down the right local structure, not by trying every possibility. We
unpack the funnel idea in module 3.

## How many distinct folds are there?

Surprisingly few. Estimates from databases like SCOP and CATH (which
classify all known tertiary structures) suggest there are only on the order
of **a few thousand** distinct fold *topologies* — even though there are
hundreds of thousands of different proteins.

This is one reason ML works as well as it does: the underlying structural
"vocabulary" is small. Many sequences map to the same fold, and a learned
model can transfer knowledge across them.

## Domains: the modular unit of folding

Most proteins longer than ~150 residues fold into multiple **domains** —
semi-independent structural units that fold on their own and often
correspond to a single function. A signalling protein might have one
domain that binds DNA, another that binds a small molecule, and a third
that anchors to the cell membrane. Each domain has its own fold from the
"thousand folds" library.

Domain decomposition matters for ML because:

- Most "single-domain" benchmarks (CASP targets, the original AlphaFold2
  paper) implicitly assume one domain.
- Multi-domain proteins have flexible linkers between domains, so the *full*
  3D structure has parts that genuinely can move relative to each other.
- Lead optimisation usually focuses on a single domain — the one that does
  the function you care about.

## Crystallography vs cryo-EM vs NMR

![Protein crystals grown in space](https://upload.wikimedia.org/wikipedia/commons/a/ad/Protein_crystals_grown_in_space.jpg)

*Protein crystals grown for X-ray crystallography. Image from Wikimedia
Commons / NASA Marshall Space Flight Center, public domain.*

Three experimental methods produced essentially every structure in the PDB
before AlphaFold2:

| Method | Strength | Limitation |
|---|---|---|
| X-ray crystallography | High resolution (≤ 2 Å) | Needs a well-ordered crystal |
| Cryo-electron microscopy | Works on huge / membrane / dynamic complexes | Resolution typically 3–4 Å |
| NMR spectroscopy | Captures dynamics in solution | Limited to smaller proteins (≤ ~25 kDa) |

![Cryo-EM image of cell lysate](https://upload.wikimedia.org/wikipedia/commons/c/c0/Cryo-EM_image_of_C._thermophilum_lysate.jpg)

*Cryo-EM begins from noisy particle images like this before reconstruction.
Image from Wikimedia Commons, Pkastrit, CC BY-SA 4.0.*

A PDB structure's resolution (in Ångströms — *lower* is better) is one of
the first things to look at. A 1.5 Å crystal structure shows you atom
positions with high confidence; a 4 Å cryo-EM map might show you the
backbone trace but only approximate side chains.

AlphaFold2 / ESMFold predictions are usually evaluated against high-resolution
crystal structures. The accuracy metric **pLDDT** that we'll meet in module
19 is essentially an attempt to mimic per-residue crystallographic
confidence.

## A note on disordered regions

Not every part of every protein folds into a stable structure. **Intrinsically
disordered regions (IDRs)** are stretches that remain floppy and adopt many
conformations dynamically. Roughly 30 % of human proteins have substantial
disordered regions, and many full proteins are intrinsically disordered.

For ML, disordered regions are tricky:

- AlphaFold2 will assign them very low pLDDT scores — its honest way of
  saying "I don't know, and the answer is probably 'no single structure
  exists'".
- Sequence-based PLMs still produce embeddings for these regions, and those
  embeddings often capture function (e.g. binding partners) even without a
  fold.
- Designing disordered proteins is its own active research area, mostly
  outside the scope of this course.
