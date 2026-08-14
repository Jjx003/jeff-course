# Hints

- Euclidean distance is `sqrt(dx*dx + dy*dy + dz*dz)`.
- Loop over each chain `H` residue and each chain `A` residue; this naturally
  avoids same-chain pairs and duplicate reversed pairs.
- A supported contact requires `min(left_confidence, right_confidence) >= 70.0`.
- Use a dictionary keyed by `(amino_acid, position)` for antigen contact counts.
- Find the maximum count, then retain every residue with that count.

## Sanity checks

- The pair at exactly `5.0` angstroms counts because the rule says "at most."
- The distant antigen residue must never appear in the contact list.
- The uncertain antigen residue must not become a candidate hotspot from uncertain
  contacts alone.
- Do not hard-code the expected residue labels; derive them from `RESIDUES`.
