## Condensation and hydrolysis in context

Peptide bond formation is thermodynamically uphill in water if considered as
a simple dehydration reaction. Cells do not build proteins by hoping amino
acids condense spontaneously. Translation uses activated intermediates and
the ribosome to couple bond formation to a larger energy flow.

Hydrolysis is also kinetically slow without catalysis. That stability is
useful: proteins should not fall apart instantly in water. Proteases solve
the kinetic problem by positioning water or another nucleophile and
stabilizing the transition state.

## Why amide resonance restricts rotation

The peptide group can be approximated as a resonance hybrid. The nitrogen is
not a simple pyramidal amine; it is closer to planar because its lone pair is
delocalized toward the carbonyl.

One way to remember the consequence:

$$
\text{more resonance} \Rightarrow \text{more planar} \Rightarrow
\text{less free rotation}
$$

This turns each peptide unit into a stiff board. The protein backbone is a
sequence of stiff boards joined at $C_\alpha$ atoms.

## Backbone torsions

For residue $i$, the main torsions are:

$$
\phi_i = C_{i-1}-N_i-C_{\alpha i}-C_i
$$

$$
\psi_i = N_i-C_{\alpha i}-C_i-N_{i+1}
$$

$$
\omega_i = C_{\alpha i}-C_i-N_{i+1}-C_{\alpha(i+1)}
$$

Most peptide bonds prefer trans $\omega$ because the two neighboring alpha
carbons are farther apart. Cis peptide bonds put them on the same side and
usually create more crowding.

## Ramachandran plots are steric maps

At each pair of $\phi$ and $\psi$ angles, atoms in adjacent residues occupy
specific positions. Some angle pairs make atoms overlap. Those are forbidden
or highly unfavorable.

Glycine has a larger allowed region because its side chain is only hydrogen.
Proline has a smaller allowed region because its ring locks the backbone
nitrogen into a narrow set of geometries.

This helps explain why sequence matters before any detailed energetic model:
different residues change the local menu of backbone shapes.

## Secondary structure from repeated torsions

An alpha helix is not magic; it is a repeated set of backbone torsion angles
plus a repeated hydrogen-bonding pattern. A beta strand is another repeated
torsion pattern. The chain can form these structures because many adjacent
residues can adopt similar allowed angles.

Later, when you see a model predict protein structure, remember that it is not
predicting arbitrary 3D spaghetti. It is predicting a structure inside a
chemically constrained space.
