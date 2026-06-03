## Hints

- `10 ** (pH - pka)` is the only exponential term you need.
- The protonated fraction should always be between 0 and 1.
- Acidic groups become more negative as pH rises.
- Basic groups become less positive as pH rises.
- `net_charge` should sum `group_charge` over every group name in the input
  list.

## Going deeper

- Try changing histidine's pKa from 6.0 to 7.0 and rerun the script. Notice how
  much its pH 7 charge changes.
- Think ahead to protein folding: burying a charged group in a nonpolar core is
  expensive unless another interaction compensates for it.
