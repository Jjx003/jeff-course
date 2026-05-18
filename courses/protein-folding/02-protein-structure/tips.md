## Going deeper

- **PDB-101 Molecule of the Month** — [https://pdb101.rcsb.org/motm/](https://pdb101.rcsb.org/motm/). One protein, every month, with figures and a story. The best free way to build structural intuition.
- **CATH classification database** — [https://www.cathdb.info/](https://www.cathdb.info/). Browse the hierarchy of known protein folds.
- **SCOP database** — [https://scop.berkeley.edu/](https://scop.berkeley.edu/). Alternative structural classification with a slightly different taxonomy.
- **Ramachandran plot interactive viewer** — [https://en.wikipedia.org/wiki/Ramachandran_plot](https://en.wikipedia.org/wiki/Ramachandran_plot). Wikipedia has good static figures; many crystallography software packages will show you the Ramachandran plot for any structure you load.
- **AlphaFold Protein Structure Database** — [https://alphafold.ebi.ac.uk/](https://alphafold.ebi.ac.uk/). Predicted structures for nearly every known protein in UniProt, with interactive 3D viewers.

## Things to look at

If you want a single concrete example to ground all of this:

- **Myoglobin** (PDB id `1MBN`) — small, single-domain, all-helix. Classic
  textbook protein.
- **Hemoglobin** (PDB id `1HHO`) — four chains, quaternary structure.
- **GFP, green fluorescent protein** (PDB id `1EMA`) — beta-barrel fold. The
  ESM3 paper uses GFP as a generation case study.
- **Lysozyme** (PDB id `1LYZ`) — mixed alpha + beta fold, with four
  disulfide bridges. The first protein to have its mechanism worked out.

You can view any of these in a browser via the **RCSB PDB website**
([https://www.rcsb.org](https://www.rcsb.org)) — paste the four-character
PDB id and you'll get an interactive 3D viewer and the raw `.pdb` file.

## Mental model

The level hierarchy is convenient for naming, but in practice it's all one
continuous physical reality. The chain has bond angles that are *literally*
the same atoms whether you describe them as "secondary structure" or "the
backbone of the tertiary fold". The boxes are useful labels for which scale
of pattern you're focused on, not separate phenomena.
