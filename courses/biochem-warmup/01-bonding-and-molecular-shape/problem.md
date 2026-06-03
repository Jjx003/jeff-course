## Why shape starts with bonding

Biochemistry is chemistry done by crowded, flexible, mostly water-soluble
molecules. Before we talk about proteins, DNA, membranes, or enzymes, we need
one habit: look at a structure and ask what the electrons are allowed to do.

![Tetrahedral geometry of methane](/courses/biochem-warmup/methane-geometry.svg)

A chemical bond is not just a line in a drawing. It is a constraint on:

- **distance**: bonded atoms sit at preferred separations.
- **rotation**: single bonds often rotate; double bonds and partial double
  bonds usually do not.
- **polarity**: unequal electron sharing creates local positive and negative
  regions.
- **shape**: the arrangement of atoms controls which contacts can form.

Those constraints are why a protein backbone has preferred torsion angles, why
amide groups are flat, and why the same atoms can behave differently in water,
inside a protein core, or near a charged residue.

## Covalent and ionic character

A **covalent bond** forms when atoms share electron density. A **pure ionic
interaction** would be full electron transfer followed by attraction between
opposite charges. Most biological bonds and contacts live between those
extremes.

The useful question is not "is this covalent or ionic?" but:

> How unevenly is electron density distributed?

When two atoms have similar attraction for electrons, sharing is fairly even.
When one atom pulls harder, the bond becomes polar:

```text
C-H   weakly polar
C-O   strongly polar
O-H   strongly polar
C-N   moderately polar
```

In biomolecules, polar covalent bonds often become recognition handles. A
carbonyl oxygen can accept a hydrogen bond. An amine can be protonated and
become positively charged. A phosphate group can carry negative charge over a
wide pH range.

## Electronegativity and polarity

**Electronegativity** measures how strongly an atom attracts shared electrons.
For our purposes, remember the rough trend:

```text
O, N, S, halogens  >  C  >  H
```

If a bond points toward an electronegative atom, that end is partially negative
($\delta^-$) and the other end is partially positive ($\delta^+$). The molecule
may then have a **dipole**, a separation of charge across space.

Polarity matters because water is polar. Polar groups can trade favorable
interactions with water for favorable interactions with each other. Nonpolar
groups cannot, so burying them away from water often becomes favorable.

## Resonance: electrons spread out

Some molecules cannot be described well by one Lewis structure. In
**resonance**, multiple drawings represent one electron distribution. The real
molecule is not flipping between drawings; the electrons are delocalized.

Common biochemical examples:

- **Carboxylate**: the negative charge is shared over two oxygens.
- **Amide**: the nitrogen lone pair overlaps with the carbonyl, giving the
  C-N bond partial double-bond character.
- **Aromatic rings**: pi electrons spread around a ring, making it flat and
  unusually stable.
- **Phosphate**: negative charge is distributed over several oxygens.

Resonance usually stabilizes charge and reduces rotation. That is why peptide
bonds are planar: the amide resonance makes the backbone less floppy than a
cartoon chain of single bonds.

## VSEPR and hybridization

**VSEPR** is the quick geometric rule: electron groups repel, so they arrange
to stay apart. A lone pair counts as an electron group even though it is not a
bond to another atom.

| Electron groups | Common geometry | Approx. angle | Hybridization |
|---|---:|---:|---|
| 2 | linear | $180^\circ$ | sp |
| 3 | trigonal planar | $120^\circ$ | sp2 |
| 4 | tetrahedral | $109.5^\circ$ | sp3 |

Hybridization is a bonding model, not a separate force. It is useful because it
connects drawings to 3D expectations:

- sp carbons are linear, as in alkynes.
- sp2 atoms are planar, as in carbonyl carbons and aromatic rings.
- sp3 atoms are tetrahedral, as in saturated carbons and many alcohol oxygens.

The shape of water is a classic VSEPR example. Oxygen has two O-H bonds and two
lone pairs, so four electron groups arrange roughly tetrahedrally. Because two
groups are lone pairs, the molecule is bent rather than tetrahedral as a whole.

## Shape as a chemical constraint

Biological molecules are not random clouds of atoms. Their shapes are strongly
biased by local bonding:

- Carbonyl carbons are flat and electrophilic.
- Amide groups are flat and less basic than amines.
- Aromatic rings are rigid, planar, and hydrophobic at their faces.
- Phosphate groups are bulky, polar, and usually anionic.
- Single bonds rotate, but steric crowding and resonance restrict rotation.

This is the first bridge toward protein folding. A protein sequence is a chain,
but each residue arrives with geometry already built in. The fold is not chosen
from every possible 3D arrangement; it is chosen from the subset that bonding,
charge, solvent, and sterics allow.

## Recap

- Bond type is a spectrum from even electron sharing to strong charge
  separation.
- Electronegativity creates polar bonds and molecular dipoles.
- Resonance delocalizes electrons, stabilizes charge, and can restrict
  rotation.
- VSEPR and hybridization give quick 3D expectations from a 2D structure.
- Molecular shape is a constraint that later folding models must respect.

Next: functional groups, the recurring chemical patterns that make large
biomolecules readable.
