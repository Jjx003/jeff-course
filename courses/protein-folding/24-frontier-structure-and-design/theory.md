## Why diffusion is a natural fit for AF3

AlphaFold2's structure module produced coordinates by composing
SE(3)-equivariant frame transformations: at each residue, the network
emits an affine transform (a rotation and translation), and successive
layers compose those transforms to build a chain. Side chains were
parameterised separately as torsion angles around each carbon-carbon
bond.

That design works beautifully for proteins, because proteins are chains
of amino-acid frames with well-defined torsion topology. It does *not*
generalise cleanly to nucleotides, free ligands, ions, or
post-translational modifications, because those entities don't have a
shared "residue frame" abstraction.

The diffusion approach steps back to a more fundamental description:
**a structure is just a cloud of atom coordinates in $\mathbb{R}^3$**.
Instead of generating coordinates through chain composition, AF3's
diffusion module trains a denoiser:

$$\hat{\mathbf{x}}_\theta(\mathbf{x}_t, t, \mathbf{z}) \approx \mathbb{E}[\mathbf{x}_0 \mid \mathbf{x}_t]$$

where $\mathbf{x}_0$ is the clean structure (atom coordinates),
$\mathbf{x}_t = \alpha_t \mathbf{x}_0 + \sigma_t \boldsymbol{\epsilon}$
is the corrupted version at noise level $t$, and $\mathbf{z}$ is the
pair representation produced by the Pairformer trunk. The training
objective is the standard denoising loss:

$$\mathcal{L} = \mathbb{E}_{t, \boldsymbol{\epsilon}}\, \lVert \hat{\mathbf{x}}_\theta(\mathbf{x}_t, t, \mathbf{z}) - \mathbf{x}_0 \rVert^2$$

At inference time the model starts from pure Gaussian noise and runs a
small number of denoising steps (typically ~20 in AF3 / Boltz-2),
conditioning each step on $\mathbf{z}$.

The crucial property is that the denoiser doesn't need to know anything
about chain topology or torsion angles. As long as the training data
contains atom positions for every entity type (protein, DNA, RNA,
ligand, ion, modified residue), the same denoiser handles them all.
That is what lets AF3 predict heterogeneous complexes with one
mechanism instead of bolting on chemistry-specific heads.

## Why the Pairformer can drop column attention

Module 15 introduced column attention as the channel through which
*co-evolutionary signal* flows: by attending across the $S$ sequences
in an MSA at each column, the model picks up which positions vary in
concert. Why is that no longer needed in AF3?

Two reasons.

First, the diffusion module places much heavier representational
demands on the pair representation $\mathbf{z}$ than AF2's structure
module did. The pair representation has to carry enough information
about distances, contacts, and orientations to denoise atom coordinates
directly. Training pressure on $\mathbf{z}$ is therefore intense, and
AF3's authors found that putting more compute into pair-side operations
(triangle attention, pair MLPs) was more productive than putting it
into MSA-side column attention.

Second, AF3 ingests **much shallower MSAs** than AF2 did — typically
hundreds of sequences vs thousands. With a shallower MSA the
co-evolutionary signal is weaker, and the bias-pair-attention channel
(modification 1 in module 15) does most of the useful work. Column
attention's marginal contribution shrinks until it becomes worth
removing.

The net effect is a simpler trunk: row attention with pair bias plus
MSA transition plus outer-product mean, no column attention. The
Pairformer block is smaller and trains faster than the Evoformer block
while producing a richer pair representation.

## A note on what diffusion is doing here

A standard intuition for diffusion in image generation: noise out the
input, learn to denoise, sample by starting from noise. The same
intuition applies to AF3's structure prediction with one twist — the
"conditioning" $\mathbf{z}$ already encodes most of the structural
content. The diffusion module is doing relatively gentle denoising on a
well-conditioned distribution, not free generation from scratch.

This is why AF3's diffusion module needs far fewer sampling steps than
an image diffusion model (~20 vs ~1000): the pair representation pins
down which residues should be close to which, so the denoiser only has
to refine that into atomic positions.

When you flip the same machinery around to generate structures (as
RFdiffusion3 does), you remove the strong conditioning and let the
denoiser handle a wider distribution. That's why RFdiffusion3 uses more
sampling steps and a larger denoiser than AF3's prediction module —
generation is a harder problem than refinement.

## Why LigandMPNN's metals jump is so large

The 77 % vs 36 % gap on metal-coordination sites is the single most
striking number in the LigandMPNN paper. The reason: metal-binding
sites are heavily constrained chemically (Zn²⁺ wants four ligands in
specific geometry; Mg²⁺ prefers six oxygens; etc.), and plain
ProteinMPNN couldn't see the metal at all — it had to *guess* from
backbone geometry alone what kind of side chains belonged there. Once
the model gets the metal as input, the choice of His / Cys / Asp / Glu
collapses to a small set determined by the metal identity and
geometry, and recovery shoots up.

This is the same general lesson as module 23's scaling wall: **giving
the model the right modality outperforms throwing more parameters at
sequence-only training**. LigandMPNN is ~10× smaller than the biggest
ESM-2 and doesn't need scaling to dominate the sequence-recovery
benchmark on its target task.

## How the AF3 → RFdiffusion3 inversion works

Treat AF3's diffusion module as a function $f_\theta$ that maps
**(pair representation, noise)** to **structure**. If the training
distribution is "real structures in PDB / AFDB", $f_\theta$ becomes a
sample from the posterior over structures conditioned on the trunk's
output.

RFdiffusion3 uses the same architectural primitive — atom-level
denoising — but trains it as a *generative* model: condition on a
*specification* (target binding pocket, target shape, target enzymatic
function) rather than on a sequence-derived pair representation. Sample
from pure noise, run more denoising steps, get a backbone (or full
atomic structure) that respects the specification.

So AF3 and RFdiffusion3 share the same atom-level diffusion backbone
and the same training mathematics; they differ in the conditioning
information and in how many sampling steps you take. This is what the
Baker lab means by "inverting AF3's framework into a generative model".

In course terms: module 15's iterative-refinement framing translates
directly. AF3 refines toward a known structure; RFdiffusion3 refines
toward a desired specification. The mechanism is the same.

## Connecting modules 15-22 to this frontier

| Module | Successor | What changed |
|---|---|---|
| Module 15 (Evoformer) | AF3 Pairformer | No column attention; deeper pair stack |
| Module 16 (outer product mean) | AF3 Pairformer | Still present, but with shallower MSA input |
| Module 17 / 18 (ESMFold) | Boltz-2 | Open AF3-class supersedes single-pass PLM folding for production |
| Module 21 (ProteinMPNN) | LigandMPNN, SolubleMPNN | Ligand + metal aware; soluble-only training |
| Module 22 (Cradle pipeline) | CRADLE-1 preprint, g-DPO paper | Same architecture, now peer-track-published |

Module 22's framing of "open research directions in 2026" is exactly
the territory this module describes. The course's earlier modules
remain accurate as pedagogy; the production defaults have moved on.
