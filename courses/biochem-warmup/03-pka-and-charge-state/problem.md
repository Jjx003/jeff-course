## Predict charge from pH and pKa

Many biomolecules change charge when pH changes. A carboxylic acid can lose a
proton and become negative. An amine can gain a proton and become positive.
Proteins contain many such groups, so even a simple pH shift can change
solubility, binding, and folding stability.

![English amino-acid charge curve](/courses/biochem-warmup/glycine-titration-curve.svg)

In this exercise, you will implement a small charge calculator using the
Henderson-Hasselbalch relationship.

For an acidic group:

$$
\mathrm{HA \rightleftharpoons H^+ + A^-}
$$

the protonated fraction is:

$$
f_\mathrm{prot} = \frac{1}{1 + 10^{\mathrm{pH} - \mathrm{p}K_a}}
$$

The expected charge of an acidic group is then:

$$
q_\mathrm{acid} = -1 \cdot (1 - f_\mathrm{prot})
$$

For a basic group:

$$
\mathrm{BH^+ \rightleftharpoons B + H^+}
$$

the same protonated fraction gives the positively charged form:

$$
q_\mathrm{base} = +1 \cdot f_\mathrm{prot}
$$

## Your task

Complete `protonated_fraction`, `group_charge`, and `net_charge`.

The starter file contains a small set of ionizable groups:

- N-terminus: basic, pKa 9.0
- C-terminus: acidic, pKa 2.2
- Asp/Glu: acidic side chains
- Lys/Arg/His: basic side chains
- Cys/Tyr: weak acidic side chains

The script prints charge estimates for short peptide-like collections of
groups at pH 2.0, 7.0, and 12.0. Values are rounded to three decimals so the
expected output is deterministic.

## Constraints

- Use only the Python standard library.
- Treat each group independently.
- Return fractional expected charges, not just integer majority states.
- Do not special-case the sample molecules; implement the general functions.
