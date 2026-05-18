## The inverse folding problem

**Forward folding** $f: \text{sequence} \to \text{structure}$ has been
the headline task since AlphaFold2. **Inverse folding** is its dual:

$$g: \text{structure} \to \text{sequence}$$

Inverse folding is **highly degenerate** — many sequences fold into
the same backbone. A typical 100-residue protein has between $10^{20}$
and $10^{40}$ sequences that would fold into roughly the same shape,
out of $20^{100} \approx 10^{130}$ possible sequences.

So the model is sampling from an exponentially-large but
biologically-meaningful subset. The objective during training is to
match the conditional distribution $p(\text{aa} \mid \text{backbone})$ over the
(relatively small) database of sequence-structure pairs in the PDB.

## ProteinMPNN architecture

ProteinMPNN (Dauparas et al, 2022) is an **encoder-decoder graph
neural network**:

1. **Encoder** ingests the backbone — every residue's CA, N, C, O
   atom positions plus the relative orientations of nearby
   residues. Outputs a per-residue feature vector that captures
   "what kind of environment is this position in".

2. **Decoder** is autoregressive over the sequence: it predicts one
   residue at a time, conditioned on the encoder context plus all
   previously sampled residues. The model uses a fixed
   **decoding order** (often the standard 1..N order) but can also
   handle random or constrained orders.

3. The output of the decoder is, for each position, a 20-way
   softmax over amino acid identities. Sample with a temperature
   parameter $\tau$ to draw a sequence:

   $$p_\tau(a \mid \text{ctx}) \propto \exp(\ell_a / \tau)$$

   - $\tau \to 0$: deterministic argmax (always pick the highest-prob
     residue).
   - $\tau = 1$: the model's natural distribution.
   - $\tau \to \infty$: uniform random.

   Higher temperature = more diverse sequences. Lower temperature =
   higher recovery but less diversity.

## Why graph networks (and not a transformer)?

ProteinMPNN uses **message passing on a k-nearest-neighbour graph**
of residues, where each residue talks to its 30-48 spatial
neighbours. This is more parameter-efficient than full
self-attention because the operations respect the locality of
backbone interactions.

Modern alternatives (ESM-IF1, AlphaFold-Inverse-Fold) use full
transformers. They're more accurate but also bigger; ProteinMPNN's
sweet spot is "small, fast, runs on a 2 GB GPU".

The encoder-decoder structure is similar to a translation model:
backbone is the source language, sequence is the target. Hayduk's
"compressed database" view (module 10) applies here too — the
training set of (backbone, sequence) pairs gets compressed into
the model's weights.

## Recovery: what it does and doesn't measure

Recovery is the fraction of positions where the sampled sequence
matches the wild-type:

$$\text{Recovery} = \frac{1}{L} \sum_{i=1}^{L} \mathbb{1}[s_i^{\text{sampled}} = s_i^{\text{wt}}]$$

It's the standard inverse-folding benchmark for two reasons:

1. **Easy to compute.** No need for fitness assays.
2. **Universally available.** Every test PDB has a known sequence.

But it has issues:

- **The model isn't optimised for recovery.** It's optimised for
  $p(\text{aa} \mid \text{backbone})$, which is a distribution over plausible
  sequences. The wild-type isn't necessarily the most likely under
  this distribution.
- **Conserved positions trivialise the score.** A handful of highly
  conserved residues (catalytic, structural cores) are easy. The
  hard positions are the surface residues with dozens of
  alternatives. Recovery doesn't distinguish.
- **Ignores *function*.** A sequence with 0% recovery might fold
  identically and have the same function. Recovery says nothing
  about it being good or bad as a design.

State of the art on the standard benchmark (a held-out subset of
the PDB):

- ProteinMPNN: 49.4 % recovery.
- ESM-IF1: 51.6 %.
- AlphaFold-Inverse-Fold (paper-only): 55+ %.

These are on test sets averaged over hundreds of proteins. For an
individual easy case (well-folded, lots of conserved residues),
recovery can hit 70-80 %; for a particularly designable backbone
with many valid sequences, recovery may be 30-40 % even for an
excellent model.

## Connecting forward and inverse folding

The ESMFold-meets-ProteinMPNN loop:

```mermaid
flowchart LR
    A["target backbone"]
    B["ProteinMPNN sample"]
    C["candidate sequence"]
    D["ESMFold"]
    E["predicted structure"]
    F["compare with target"]

    A --> B --> C --> D --> E --> F
    F -. accept .-> G["select for wet lab"]
    F -. reject .-> B
```

This is the **filter** step: many ProteinMPNN samples are biologically
plausible but might not fold into the *exact* target. Folding them
back with ESMFold and computing RMSD/TM-score (module 19) lets you
filter to sequences that pass the round trip.

A typical protein-design pipeline:

1. Start with a target backbone (designed in RFdiffusion or borrowed
   from PDB).
2. Sample 100-1000 sequences via ProteinMPNN at $\tau = 0.1$.
3. Fold each with ESMFold; keep those with TM-score > 0.9 to the
   target backbone.
4. Score each with ESM-2 PLL (module 20) for "general protein
   plausibility".
5. Rank by combined score; pick top-10 for wet lab.

The Cradle pipeline (module 22) inserts an **assay-conditioned
predictor** between steps 3 and 5, so the score weights
"plausibility" and "in-vitro fitness" together.

## Why expression matters

ProteinMPNN sequences usually express better in *E. coli* than the
wild-type they're "designed from". The model learned the
composition statistics of well-expressing soluble proteins (more
charged surface residues, fewer cysteines, balanced
hydrophobicity), and bakes those statistics into every sample.

Side observations from the original paper:

- Average net charge of ProteinMPNN sequences is more negative than
  WT, presumably reflecting *E. coli* expression bias in the
  training set.
- Cysteine usage is significantly lower than WT.
- Glycine and proline at loops are frequently substituted for other
  small residues — the model effectively replaces flexibility-
  enabling residues with rigidity-enabling ones.

These biases are useful: ProteinMPNN-redesigned sequences are
typically easier to express and more thermostable than wild-type.

## Beyond recovery: real evaluation

In practice, you evaluate inverse-folding output by:

1. **Forward-fold** the sampled sequence and compare to the input
   backbone (TM-score > 0.9).
2. **Express in lab** and check solubility / stability.
3. **Functional assay** — does it bind / catalyse / fluoresce?

ProteinMPNN paper showed step 3 success rates of 50-90 % across
several test cases (de novo binders, enzymes, miniproteins). That's
remarkable — sampling from a generative model and getting
functional proteins half the time, no MSA needed, no per-target
fine-tuning.

## Failure modes

- **Membrane proteins.** The training set is dominated by soluble
  proteins; ProteinMPNN samples are biased toward soluble-protein
  composition, which for membrane proteins is wrong.
- **Multi-domain proteins.** The model handles single chains well
  but struggles with inter-domain interfaces.
- **Very short sequences (< 20 residues).** Low recovery just
  because each position has many valid alternatives.
- **Backbones that don't actually fold.** ProteinMPNN happily
  generates sequences for impossible backbones; the round-trip
  test (forward-fold check) is essential.

## ESM-IF1 and others

ESM-IF1 (Hsu et al, 2022) uses a transformer instead of GNN, larger
training set (incorporating AlphaFold2 predictions to augment the
PDB), and reports ~52 % recovery vs ProteinMPNN's 49 %. Both are
"fine for most users". Choose ProteinMPNN for low-VRAM or older
workflow; choose ESM-IF1 if you already have ESM infrastructure
and want the marginal accuracy.

AlphaFold-3 includes inverse folding capabilities natively (Abramson
et al, 2024). It's the highest-quality option and supports
multi-chain and ligand-conditioned design, but only via
DeepMind's hosted server.

For most ML-meets-biology projects today, ProteinMPNN remains the
default because it's small, fast, accurate enough, and runs locally.
