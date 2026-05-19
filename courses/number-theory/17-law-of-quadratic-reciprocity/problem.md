# The Law of Quadratic Reciprocity

We have seen that Euler's Criterion provides a way to compute the Legendre symbol $\left(\frac{a}{p}\right)$. However, for large values of $a$ and $p$, computing $a^{\frac{p-1}{2}} \pmod p$ can still be tedious by hand. 

More profoundly, mathematicians in the 18th century noticed a striking, symmetric pattern when comparing whether a prime $p$ is a quadratic residue modulo another prime $q$, and whether $q$ is a quadratic residue modulo $p$.

This observation led to the **Law of Quadratic Reciprocity**, first fully proven by Carl Friedrich Gauss, who called it the "Aureum Theorema" (Golden Theorem).

The Law of Quadratic Reciprocity allows us to flip the Legendre symbol $\left(\frac{p}{q}\right)$ into $\left(\frac{q}{p}\right)$, vastly simplifying the computation of quadratic residues and revealing a deep, unexpected connection between prime numbers.

## Learning Objectives

- State the Law of Quadratic Reciprocity.
- Understand the First and Second Supplements to the Law.
- Learn Gauss's Lemma, a key stepping stone to proving the Law.
- Use Reciprocity to rapidly evaluate Legendre symbols.
