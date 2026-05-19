# The Theory of Quadratic Residues

For a given odd prime $p$, consider the congruence:

$$
x^2 \equiv a \pmod p
$$

If $\gcd(a, p) = 1$, we say that $a$ is a **quadratic residue** modulo $p$ if the congruence has a solution. If it does not have a solution, $a$ is called a **quadratic nonresidue**.

For example, let $p = 7$. We can square the integers $1$ through $6$ modulo $7$:

- $1^2 \equiv 1 \pmod 7$
- $2^2 \equiv 4 \pmod 7$
- $3^2 \equiv 9 \equiv 2 \pmod 7$
- $4^2 \equiv 16 \equiv 2 \pmod 7$
- $5^2 \equiv 25 \equiv 4 \pmod 7$
- $6^2 \equiv 36 \equiv 1 \pmod 7$

The quadratic residues modulo 7 are $\{1, 2, 4\}$. The quadratic nonresidues are $\{3, 5, 6\}$. Notice that exactly half of the non-zero integers are residues, and exactly half are nonresidues. Furthermore, $x^2 \equiv (p-x)^2 \pmod p$, so the squares are symmetric.

## The Legendre Symbol

To elegantly express whether $a$ is a quadratic residue, Adrien-Marie Legendre introduced the **Legendre symbol**, denoted as $\left(\frac{a}{p}\right)$. It is defined for an odd prime $p$ and an integer $a$ as follows:

$$
\left(\frac{a}{p}\right) = \begin{cases} 
1 & \text{if } a \text{ is a quadratic residue modulo } p \text{ and } a \not\equiv 0 \pmod p \\
-1 & \text{if } a \text{ is a quadratic nonresidue modulo } p \\
0 & \text{if } a \equiv 0 \pmod p
\end{cases}
$$

The Legendre symbol is completely multiplicative:

$$
\left(\frac{ab}{p}\right) = \left(\frac{a}{p}\right)\left(\frac{b}{p}\right)
$$

This means:
- The product of two residues is a residue.
- The product of two nonresidues is a residue.
- The product of a residue and a nonresidue is a nonresidue.

## Euler's Criterion

Leonhard Euler discovered a beautiful relationship that allows us to compute the Legendre symbol directly.

**Theorem (Euler's Criterion):** Let $p$ be an odd prime and $a$ be an integer not divisible by $p$. Then:

$$
\left(\frac{a}{p}\right) \equiv a^{\frac{p-1}{2}} \pmod p
$$

### Proof of Euler's Criterion

Let's prove this rigorously. By Fermat's Little Theorem, we know that:

$$
a^{p-1} \equiv 1 \pmod p
$$

Since $p$ is an odd prime, $p-1$ is even, so we can factor this equation as a difference of squares:

$$
a^{p-1} - 1 = \left(a^{\frac{p-1}{2}} - 1\right)\left(a^{\frac{p-1}{2}} + 1\right) \equiv 0 \pmod p
$$

Since $p$ is prime, it must divide one of the factors. Therefore:

$$
a^{\frac{p-1}{2}} \equiv 1 \pmod p \quad \text{or} \quad a^{\frac{p-1}{2}} \equiv -1 \pmod p
$$

**Case 1: $a$ is a quadratic residue.**
If $a$ is a quadratic residue, there exists some integer $x$ such that $x^2 \equiv a \pmod p$. Substituting this into our expression gives:

$$
a^{\frac{p-1}{2}} \equiv (x^2)^{\frac{p-1}{2}} \equiv x^{p-1} \pmod p
$$

By Fermat's Little Theorem (since $x \not\equiv 0 \pmod p$), we have $x^{p-1} \equiv 1 \pmod p$. Thus, $a^{\frac{p-1}{2}} \equiv 1 \pmod p$, matching the Legendre symbol definition.

**Case 2: $a$ is a quadratic nonresidue.**
If $a$ is a nonresidue, we can pair up the integers from $1$ to $p-1$. For any $i \in \{1, 2, \dots, p-1\}$, the linear congruence $i \cdot j \equiv a \pmod p$ has a unique solution $j$ in the same range. 

Because $a$ is a nonresidue, we know that $i \neq j$ (otherwise $i^2 \equiv a \pmod p$, making $a$ a residue). Thus, the numbers $1, \dots, p-1$ group into exactly $\frac{p-1}{2}$ distinct pairs $(i, j)$ such that $i \cdot j \equiv a \pmod p$.

Multiplying all these pairs together gives the product of all integers from $1$ to $p-1$, which is $(p-1)!$. On the other hand, it also equals the product of the $\frac{p-1}{2}$ copies of $a$:

$$
(p-1)! \equiv a^{\frac{p-1}{2}} \pmod p
$$

By **Wilson's Theorem**, $(p-1)! \equiv -1 \pmod p$. Therefore:

$$
-1 \equiv a^{\frac{p-1}{2}} \pmod p
$$

This completes the proof. Euler's Criterion is mathematically elegant and gives us a deterministic algorithm to test for quadratic residues using modular exponentiation.

## Example

Let's use Euler's Criterion to find if 5 is a quadratic residue modulo 11.
We compute $5^{\frac{11-1}{2}} = 5^5 \pmod{11}$.

$$
5^2 = 25 \equiv 3 \pmod{11}
$$

$$
5^4 = (5^2)^2 \equiv 3^2 = 9 \equiv -2 \pmod{11}
$$

$$
5^5 = 5^4 \cdot 5 \equiv (-2) \cdot 5 = -10 \equiv 1 \pmod{11}
$$

Since $5^5 \equiv 1 \pmod{11}$, $5$ is a quadratic residue modulo 11. Indeed, $4^2 = 16 \equiv 5 \pmod{11}$.
