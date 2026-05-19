# The Thermodynamics of Folding

<p align="center">
  <img src="/images/protein-folding/folding-funnel.svg" alt="Folding Funnel Energy Landscape" />
</p>

## Breaking down $\Delta G$

The total free energy change on folding is conventionally decomposed into
contributions from different physical interactions:

$$
\Delta G_{\text{fold}} = \Delta G_{\text{hydrophobic}} + \Delta G_{\text{H-bonds}}
+ \Delta G_{\text{electrostatic}} + \Delta G_{\text{van der Waals}}
- T \Delta S_{\text{conformational}}
$$

Approximate magnitudes for a small (~100-residue) globular protein:

| Term | Sign | Magnitude (kcal/mol) | Comment |
|---|---|---|---|
| Hydrophobic | favourable | $-50$ to $-100$ | Dominant driver |
| Hydrogen bonds (net) | small favourable | $-5$ to $-15$ | Each ~0.5–1.5 kcal; many bonds, but unfolded chain has H-bonds to water too |
| Electrostatics | small | $\pm 5$ | Salt bridges contribute a little; long-range repulsion can hurt |
| van der Waals (packing) | small favourable | $-5$ to $-10$ | Tight packing in the core |
| Conformational entropy | unfavourable | $+50$ to $+100$ | Folded chain is much more ordered |
| **Total** | **favourable** | **$-5$ to $-15$** | Always close to zero! |

The dramatic cancellation between the large favourable terms (hydrophobic,
packing, H-bonds) and the large unfavourable entropy term is what makes
proteins marginally stable. Evolution has tuned them to be *just* stable
enough to function and no more, presumably so they can be efficiently
degraded and replaced.

## Why so marginal?

The biological explanation for marginal stability: cells *need* to turn
proteins over. Stable cellular function requires regulated protein
degradation (via the proteasome). A protein that was $-100\ \text{kcal/mol}$
stable would be impossible to unfold and recycle.

Marginal stability is also a feature for evolution. A typical missense
mutation changes $\Delta G_{\text{fold}}$ by about $\pm 1\ \text{kcal/mol}$.
If the wild-type protein has $\Delta G = -10\ \text{kcal/mol}$, a small
fraction of mutations push it to instability ($\Delta G \ge 0$) but most
leave it functional. This is exactly the kind of softness that lets a
protein family explore sequence space without losing function — and it's
why **most random single-point mutations are tolerated**, a fact the
g-DPO method in module 22 exploits.

## The Levinthal-funnel reconciliation

Levinthal's paradox (1968): a protein of length $L$ has roughly $10^L$
conformations; even at $10^{13}$ samples per second, exhaustive search
would take longer than the age of the universe. Yet proteins fold in
milliseconds.

The folding funnel resolves this as follows. The chain doesn't sample
configurations independently — it samples them in correlated, biased ways
because:

1. Hydrophobic collapse is fast (sub-millisecond). The chain quickly
   coalesces into a "molten globule" with the right rough shape.
2. Local secondary structure forms next, biased by the local sequence.
3. The molten globule then progressively tightens into the native fold.

Each step *prunes* huge swaths of the conformation space. By the time you
get to step 3, only a tiny fraction of the original $10^L$ possibilities
are still on the table.

## Molecular dynamics: the brute-force alternative

If you want to simulate folding from first principles, the tool is
**molecular dynamics (MD)**. You write down a force field (a classical
potential energy function based on bond stretches, angles, torsions,
electrostatics, van der Waals), put the protein in a box of explicit water,
and integrate Newton's equations of motion in tiny ($\sim 1\ \text{fs}$)
timesteps.

Folding a small protein takes about $1\ \mu\text{s}$ of *biological* time,
which is $10^9$ MD steps. Each step requires computing forces between every
pair of atoms in the system (the protein plus thousands of waters). On a
modern GPU you can simulate roughly $1\ \mu\text{s/day}$ for a small
system, so folding a small protein from scratch takes about a day of GPU
time. Anything bigger takes weeks.

This is what folks did before AlphaFold2. The famous **D. E. Shaw Research**
Anton supercomputer was purpose-built for MD; the **Folding@home** project
crowdsources MD compute on volunteers' computers worldwide. The accuracy is
respectable but the throughput is laughable compared to ML predictions.

ML structure prediction is so dominant now because it replaces $10^9$ MD
steps with a single forward pass of a neural network. The trade-off is
that ML doesn't tell you anything about *dynamics* — it gives you the
folded structure, not the trajectory. For dynamics questions (which
fluctuations matter for catalysis, how the protein responds to ligand
binding) people still use MD, often *starting from* an AlphaFold2-predicted
structure.

## Chaperones and the "folding code" caveat

A non-negligible minority of proteins need help to fold. The two main
classes:

- **Hsp70 / Hsp90 family** — bind newly synthesised polypeptides and hold
  them in folding-competent conformations.
- **GroEL/GroES (in bacteria) / CCT (in eukaryotes)** — barrel-shaped
  chambers that sequester misfolded clients away from the cytoplasm and
  give them another shot at folding correctly.

Chaperones don't add structural information that isn't in the sequence —
they just lower the kinetic barriers. So Anfinsen's dogma still holds in
the thermodynamic sense, but on a short enough timescale, some proteins
*kinetically* require chaperones to find their native fold within their
lifetime in the cell.

For ML, this matters in one subtle way: training data is biased toward
proteins that *did* fold without chaperone assistance (because that's what
shows up in the PDB). Proteins that absolutely require chaperones may be
underrepresented and harder to predict.

## Cold denaturation: the other end

Heating a protein unfolds it. So does, surprisingly, **cooling it enough**.
At sufficiently low temperature, the hydrophobic effect weakens (water gets
more ordered around hydrophobic surfaces *without* needing the side chain
to be exposed) and the protein loses stability.

Most proteins are most stable somewhere between $0°\ \text{C}$ and
$30°\ \text{C}$. This is just a curious thermodynamic fact, but it's a
reminder that "folded" isn't a binary state — every protein has a
**stability curve** $\Delta G(T)$ that peaks at some temperature.

This is relevant for ML prediction in that the training data is mostly
proteins folded at $20$ to $37°\ \text{C}$. Predicting structures at
extreme temperatures (thermophiles, psychrophiles) is harder.
