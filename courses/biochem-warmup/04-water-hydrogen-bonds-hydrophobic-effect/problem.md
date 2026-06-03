## Water is the background force field of biology

Most biomolecules operate in water. That sounds ordinary until you remember
that water is not passive space. It is polar, cohesive, hydrogen-bonded, and
constantly reorganizing around every exposed surface.

Protein folding, membrane formation, ligand binding, and DNA structure all
depend on what water can and cannot comfortably solvate.

## Water structure

Water has two polar O-H bonds and two lone pairs on oxygen. Its electron groups
are arranged roughly tetrahedrally, giving a bent molecule with a strong dipole.

![Water molecules connected by hydrogen bonds](/courses/biochem-warmup/water-hbond-network.svg)

Each water molecule can, in principle:

- donate two hydrogen bonds through its O-H hydrogens.
- accept two hydrogen bonds through oxygen lone pairs.

Liquid water is not a static lattice. Hydrogen bonds break and reform rapidly,
but the network is structured enough that disrupting it has thermodynamic
consequences.

## Hydrogen-bond geometry

A hydrogen bond is strongest when the donor, hydrogen, and acceptor are close
to linear:

```text
D-H ... A
```

where `D` is a donor atom such as O or N, and `A` is an acceptor atom such as O
or N with a lone pair.

Good hydrogen bonds are directional. This matters in proteins because backbone
hydrogen bonds are not generic sticky contacts; helices and sheets work because
the atoms line up in repeatable geometries.

## Solvation shells

When an ion or polar group is exposed to water, nearby water molecules orient
around it. This local arrangement is a **solvation shell**.

- Around a cation, water oxygens point inward.
- Around an anion, water hydrogens point inward.
- Around polar neutral groups, water aligns to donate or accept hydrogen bonds.

These interactions are often favorable enough that moving a charged group from
water into a nonpolar protein interior is costly unless the protein supplies
replacement interactions.

## The hydrophobic effect

Nonpolar groups do not form strong hydrogen bonds with water. Water can still
surround them, but it must give up some freedom to maintain its own hydrogen
bond network near the nonpolar surface.

When several nonpolar groups cluster together, the total nonpolar surface area
exposed to water decreases. Fewer water molecules are forced into constrained
solvation shells. The system gains entropy:

$$
\Delta G = \Delta H - T\Delta S
$$

The hydrophobic effect is not mainly because nonpolar groups strongly attract
each other. It is largely because water prefers not to organize around exposed
nonpolar surface.

## Amphipathic molecules

An **amphipathic** molecule has both polar and nonpolar regions. This split
creates self-assembly:

- fatty acids form micelles or membranes.
- phospholipids form bilayers.
- proteins bury many nonpolar side chains while exposing polar and charged
  groups.

![A lipid micelle with hydrophilic surface and hydrophobic interior](/courses/biochem-warmup/lipid-micelle.svg)

The key is not "water hates oil" as an emotion. The key is that water's own
hydrogen-bond network makes some arrangements more favorable than others.

## Why nonpolar groups bury

Inside many soluble proteins, hydrophobic residues such as Val, Leu, Ile, Met,
Phe, and Trp are enriched in the core. Polar and charged residues are enriched
on the surface.

This pattern is statistical, not absolute. A buried polar group can be stable
if it forms hydrogen bonds or salt bridges. A hydrophobic patch can remain
surface-exposed if it binds a membrane, another protein, or a ligand.

Still, the baseline rule is powerful:

> In water, burying nonpolar surface can be favorable because it releases
> ordered water.

That rule is one of the first physical reasons a protein sequence can collapse
from an extended chain into a compact fold.

## Recap

- Water is polar and forms a dynamic hydrogen-bond network.
- Hydrogen bonds are directional and geometry-sensitive.
- Solvation shells organize water around ions and polar groups.
- The hydrophobic effect is largely an entropy effect of water release.
- Amphipathic molecules self-organize by exposing polar regions and hiding
  nonpolar ones.

Next, these ideas will combine with amino acid chemistry to explain why protein
sequences have folding preferences.
