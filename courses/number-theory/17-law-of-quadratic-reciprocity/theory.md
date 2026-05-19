# Quadratic Reciprocity and Gauss's Lemma

The Law of Quadratic Reciprocity connects the solvability of $x^2 \equiv p \pmod q$ with $x^2 \equiv q \pmod p$.

**Theorem (The Law of Quadratic Reciprocity):**
Let $p$ and $q$ be distinct odd primes. Then:

$$
\left(\frac{p}{q}\right) \left(\frac{q}{p}\right) = (-1)^{\frac{p-1}{2} \cdot \frac{q-1}{2}}
$$

Alternatively, we can write this as:

$$
\left(\frac{p}{q}\right) = \begin{cases} 
\left(\frac{q}{p}\right) & \text{if } p \equiv 1 \pmod 4 \text{ or } q \equiv 1 \pmod 4 \\
-\left(\frac{q}{p}\right) & \text{if } p \equiv 3 \pmod 4 \text{ and } q \equiv 3 \pmod 4
\end{cases}
$$

This means that unless *both* $p$ and $q$ are congruent to $3 \pmod 4$, they share the same quadratic character relative to each other (i.e., $p$ is a residue mod $q$ if and only if $q$ is a residue mod $p$). If both are $3 \pmod 4$, exactly one is a residue of the other!

## The Supplements

The Law relates two odd primes. But what about the primes $2$ and $-1$? For these, we have the "supplements" to the Law of Quadratic Reciprocity:

**First Supplement:** 
For an odd prime $p$:

$$
\left(\frac{-1}{p}\right) = (-1)^{\frac{p-1}{2}} = \begin{cases} 
1 & \text{if } p \equiv 1 \pmod 4 \\
-1 & \text{if } p \equiv 3 \pmod 4
\end{cases}
$$
This tells us that $-1$ is a perfect square modulo $p$ exactly when $p \equiv 1 \pmod 4$. (Note: We actually already proved this using Euler's Criterion!)

**Second Supplement:**
For an odd prime $p$:

$$
\left(\frac{2}{p}\right) = (-1)^{\frac{p^2-1}{8}} = \begin{cases} 
1 & \text{if } p \equiv 1, 7 \pmod 8 \\
-1 & \text{if } p \equiv 3, 5 \pmod 8
\end{cases}
$$

## Gauss's Lemma

To prove the Law of Quadratic Reciprocity, Gauss introduced a clever combinatorial lemma.

**Gauss's Lemma:** Let $p$ be an odd prime and let $a$ be an integer not divisible by $p$. Consider the set of integers:
$$
S = \left\{ a, 2a, 3a, \dots, \frac{p-1}{2}a \right\}
$$
Reduce each element of $S$ modulo $p$ to lie in the range $[-\frac{p-1}{2}, \frac{p-1}{2}]$. Let $n$ be the number of negative values in this resulting set. Then:

$$
\left(\frac{a}{p}\right) = (-1)^n
$$

### Example of Gauss's Lemma

Let $p = 11$ and $a = 7$.
The set $S$ is $\{ 7(1), 7(2), 7(3), 7(4), 7(5) \} = \{ 7, 14, 21, 28, 35 \}$.
We reduce these modulo $11$ into the range $[-5, 5]$:
- $7 \equiv -4 \pmod{11}$
- $14 \equiv 3 \pmod{11}$
- $21 \equiv -1 \pmod{11}$
- $28 \equiv 6 \equiv -5 \pmod{11}$
- $35 \equiv 2 \pmod{11}$

The resulting set is $\{-4, 3, -1, -5, 2\}$.
The number of negative elements is $n = 3$.
By Gauss's Lemma, $\left(\frac{7}{11}\right) = (-1)^3 = -1$.
Indeed, $7$ is a quadratic nonresidue modulo $11$.

## Putting it into Practice

Using Reciprocity and the Supplements, computing Legendre symbols becomes a game of "flip and reduce."

Example: Compute $\left(\frac{14}{43}\right)$.

1. Factor out the $2$: $\left(\frac{14}{43}\right) = \left(\frac{2}{43}\right) \left(\frac{7}{43}\right)$.
2. Compute $\left(\frac{2}{43}\right)$: Since $43 \equiv 3 \pmod 8$, the Second Supplement gives $\left(\frac{2}{43}\right) = -1$.
3. Compute $\left(\frac{7}{43}\right)$: Apply the Law of Quadratic Reciprocity. Both $7$ and $43$ are $\equiv 3 \pmod 4$. So we flip and negate:
   $$
   \left(\frac{7}{43}\right) = -\left(\frac{43}{7}\right)
   $$
4. Reduce modulo $7$: $43 \equiv 1 \pmod 7$, so $\left(\frac{43}{7}\right) = \left(\frac{1}{7}\right) = 1$.
5. Therefore, $\left(\frac{7}{43}\right) = -1$.
6. Multiply them together: $\left(\frac{14}{43}\right) = (-1)(-1) = 1$.

So $14$ is a quadratic residue modulo $43$.
