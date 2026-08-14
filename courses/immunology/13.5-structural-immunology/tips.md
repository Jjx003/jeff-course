# Structure-to-function review card

For every structural claim, record:

- what entities and biological state were modeled;
- confidence at the relevant residue and interface;
- whether glycosylation, membrane context, cofactors, or modifications are missing;
- the closest related structures in training or templates;
- a mutation predicted to disrupt the interaction;
- a control for expression and global folding;
- separate binding and cellular-function assays;
- a rescue or orthogonal validation;
- the organism-level claim that remains untested.

## Common traps

- treating high pLDDT as proof of a complex interface;
- using docking geometry as a substitute for affinity or kinetics;
- inferring natural peptide presentation from peptide-MHC compatibility;
- calling loss of binding direct escape without a fold/expression control;
- optimizing affinity while ignoring specificity, density, tissue, or Fc context;
- assuming a designed sequence is non-immunogenic because it folds as intended.

The shortest useful sentence is: **the model predicts a testable contact, not the
final immune outcome.**
