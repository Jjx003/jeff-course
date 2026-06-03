## Henderson-Hasselbalch intuition

The Henderson-Hasselbalch equation is usually written:

$$
\mathrm{pH} = \mathrm{p}K_a + \log_{10}\left(\frac{[\mathrm{A^-}]}{[\mathrm{HA}]}\right)
$$

It says that pH compares the solution's proton availability to a group's pKa.

- If $\mathrm{pH} = \mathrm{p}K_a$, the group is 50% protonated.
- If $\mathrm{pH} < \mathrm{p}K_a$, protonated forms are favored.
- If $\mathrm{pH} > \mathrm{p}K_a$, deprotonated forms are favored.

The same fraction formula works for acids and bases:

$$
f_\mathrm{prot} = \frac{1}{1 + 10^{\mathrm{pH} - \mathrm{p}K_a}}
$$

The difference is what protonation means for charge.

## Acids and bases have opposite charge logic

For an acidic group such as a carboxyl:

```text
R-COOH  <->  R-COO^- + H^+
neutral      negative
```

Protonated means neutral; deprotonated means negative.

For a basic group such as an amine:

```text
R-NH3^+  <->  R-NH2 + H^+
positive      neutral
```

Protonated means positive; deprotonated means neutral.

So:

$$
q_\mathrm{acid} = -(1 - f_\mathrm{prot})
$$

$$
q_\mathrm{base} = f_\mathrm{prot}
$$

## Amino acid charge intuition

At about pH 7:

- Asp and Glu are usually negative.
- Lys and Arg are usually positive.
- His is partly protonated and often sensitive to local environment.
- Cys and Tyr are usually neutral, but can lose protons at high pH or in
  special active sites.
- Protein termini matter for short peptides but are a smaller fraction of a
  large protein.

Real proteins are not just sums of isolated pKa values. Burial, nearby charges,
hydrogen bonds, and metal ions can shift pKa dramatically. Still, this isolated
model is the baseline you need before interpreting more complex behavior.
