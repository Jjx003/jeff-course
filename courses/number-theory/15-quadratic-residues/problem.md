# Quadratic Residues

We've explored modular arithmetic, focusing primarily on linear equations of the form $ax \equiv b \pmod n$. But what happens when we introduce exponents? The simplest non-linear congruence is a quadratic one:

$$
x^2 \equiv a \pmod p
$$

Given a prime $p$ and an integer $a$, does there exist an integer $x$ that satisfies this equation? 

If such an $x$ exists, we say that $a$ is a **quadratic residue** modulo $p$. If no such $x$ exists, $a$ is called a **quadratic nonresidue**.

In this module, we will formalize the concept of quadratic residues and introduce **Euler's Criterion**, a powerful mathematical tool to determine whether an integer is a quadratic residue without having to test all possible values of $x$.

## Learning Objectives

- Define quadratic residues and nonresidues modulo $p$.
- Understand the definition and properties of the **Legendre symbol**.
- Prove and apply **Euler's Criterion** to test for quadratic residues.

Let's dive into the theory and uncover the structure of squares modulo $p$.
