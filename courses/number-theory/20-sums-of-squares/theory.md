### Fermat's Theorem on Sums of Two Squares

Let's look at small primes and see which can be written as $x^2 + y^2$:

- $2 = 1^2 + 1^2$ (Yes)
- $3$ (No)
- $5 = 2^2 + 1^2$ (Yes)
- $7$ (No)
- $11$ (No)
- $13 = 3^2 + 2^2$ (Yes)
- $17 = 4^2 + 1^2$ (Yes)
- $19$ (No)

A pattern emerges: odd primes $p$ can be written as $x^2 + y^2$ if and only if $p \equiv 1 \pmod 4$.

**Theorem (Fermat, 1640):** An odd prime $p$ is expressible as the sum of two squares if and only if $p \equiv 1 \pmod 4$.

#### The Proof

**Part 1: The "Only If" direction.**
Assume $p = x^2 + y^2$. Since $p$ is odd, one of $x, y$ is even and the other is odd. Suppose $x = 2k$ and $y = 2m + 1$. 

$$
x^2 + y^2 = 4k^2 + 4m^2 + 4m + 1 = 4(k^2 + m^2 + m) + 1
$$

Thus, $p \equiv 1 \pmod 4$.

**Part 2: The "If" direction (using Thue's Lemma).**
Assume $p \equiv 1 \pmod 4$. By the properties of Legendre symbols, $\left(\frac{-1}{p}\right) = 1$. Thus, there exists an integer $z$ such that $z^2 \equiv -1 \pmod p$.

**Thue's Lemma** states that for any integer $z$ and prime $p$, there exist integers $x, y$ such that $0 < |x|, |y| < \sqrt{p}$ and $x \equiv zy \pmod p$.

Let's apply Thue's Lemma to our $z$. We have $x \equiv zy \pmod p$, so squaring both sides:

$$
x^2 \equiv z^2 y^2 \equiv (-1)y^2 \pmod p
$$

$$
x^2 + y^2 \equiv 0 \pmod p
$$

This means $x^2 + y^2$ is a multiple of $p$. But we also bounded $x$ and $y$:

$$
0 < x^2 + y^2 < (\sqrt{p})^2 + (\sqrt{p})^2 = 2p
$$

The only multiple of $p$ strictly between $0$ and $2p$ is $p$ itself! Therefore, $x^2 + y^2 = p$. $\blacksquare$

### Sums of Two Squares for Any Integer

Thanks to Brahmagupta's identity, the product of two sums of squares is also a sum of squares:

$$
(a^2 + b^2)(c^2 + d^2) = (ac - bd)^2 + (ad + bc)^2
$$

This leads to the general theorem:
**Theorem:** An integer $n \ge 1$ can be expressed as the sum of two squares if and only if every prime factor $p$ of $n$ such that $p \equiv 3 \pmod 4$ occurs with an **even** exponent in the prime factorization of $n$.

### Lagrange's Four-Square Theorem

While not every number is the sum of two or even three squares (e.g., 7 requires four), Joseph-Louis Lagrange proved in 1770 that four squares are always enough!

**Theorem (Lagrange, 1770):** Every positive integer $n$ can be expressed as the sum of four integer squares: $n = a^2 + b^2 + c^2 + d^2$.

The proof relies on Euler's four-square identity (analogous to Brahmagupta's identity), which shows that the product of two sums of four squares is again a sum of four squares. Because of this identity, it suffices to prove the theorem for prime numbers.

The proof for primes proceeds by showing that for any prime $p$, there exist $a, b$ such that $a^2 + b^2 + 1^2 + 0^2 \equiv 0 \pmod p$. From there, an elegant infinite descent argument (similar to Fermat's technique) allows us to shrink the multiple of $p$ until we achieve exactly $p = x^2 + y^2 + z^2 + w^2$.
