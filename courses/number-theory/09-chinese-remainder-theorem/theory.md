# Formalizing the Chinese Remainder Theorem

### The Theorem Statement

Let $m_1, m_2, \dots, m_k$ be pairwise coprime positive integers. This means that for any $i \neq j$, the greatest common divisor $\gcd(m_i, m_j) = 1$.

Let $a_1, a_2, \dots, a_k$ be any integers. Then the system of congruences:

$$
\begin{cases}
x \equiv a_1 \pmod{m_1} \\
x \equiv a_2 \pmod{m_2} \\
\vdots \\
x \equiv a_k \pmod{m_k}
\end{cases}
$$

has a solution, and this solution is unique modulo $M$, where $M = m_1 \cdot m_2 \cdots m_k$.

### Constructive Proof

We will prove this by explicitly constructing a solution $x$.

**Step 1: Define the total modulus $M$.**
Let $M = m_1 m_2 \cdots m_k = \prod_{i=1}^k m_i$.

**Step 2: Define partial products $M_i$.**
For each $i$ from 1 to $k$, define $M_i = \frac{M}{m_i}$. 
Notice that $M_i$ is the product of all moduli *except* $m_i$. Therefore, $M_i$ is a multiple of $m_j$ for all $j \neq i$.
Because the moduli are pairwise coprime, $\gcd(M_i, m_i) = 1$.

**Step 3: Find the modular inverse $y_i$.**
Since $\gcd(M_i, m_i) = 1$, we know from Bezout's Identity that $M_i$ has a multiplicative inverse modulo $m_i$. 
Let $y_i$ be this inverse, such that:

$$
M_i y_i \equiv 1 \pmod{m_i}
$$

**Step 4: Construct the solution.**
We propose the following solution:

$$
x = \sum_{i=1}^k a_i M_i y_i
$$

**Step 5: Verify the solution.**
We need to check that this $x$ satisfies $x \equiv a_j \pmod{m_j}$ for any chosen $j$.
Let's consider the terms in the sum modulo $m_j$:
For $i \neq j$, $M_i$ contains $m_j$ as a factor. Therefore, $a_i M_i y_i \equiv 0 \pmod{m_j}$.
For $i = j$, the term is $a_j M_j y_j$. Since $M_j y_j \equiv 1 \pmod{m_j}$, this term is congruent to $a_j \pmod{m_j}$.

Thus, the entire sum modulo $m_j$ collapses to:

$$
x \equiv 0 + 0 + \dots + a_j(1) + \dots + 0 \equiv a_j \pmod{m_j}
$$

This shows that our constructed $x$ is indeed a solution.

### Uniqueness

To show the solution is unique modulo $M$, suppose there are two solutions, $x$ and $y$.
Then for each $i$:

$$
x \equiv a_i \pmod{m_i}
$$

$$
y \equiv a_i \pmod{m_i}
$$

This implies $x - y \equiv 0 \pmod{m_i}$, meaning $m_i$ divides $(x - y)$ for all $i$.
Since the $m_i$ are pairwise coprime, their product $M$ must also divide $(x - y)$.
Therefore, $x \equiv y \pmod{M}$.

### Example: Sun Tzu's Problem

Let's solve the problem from the introduction:

$$
x \equiv 2 \pmod{3}
$$

$$
x \equiv 3 \pmod{5}
$$

$$
x \equiv 2 \pmod{7}
$$

Here, $m_1=3, m_2=5, m_3=7$ and $a_1=2, a_2=3, a_3=2$.
$M = 3 \times 5 \times 7 = 105$.

- **For $i=1$**: $M_1 = 105/3 = 35$. We need $y_1$ such that $35 y_1 \equiv 1 \pmod{3}$.
  Since $35 \equiv 2 \pmod{3}$, we solve $2 y_1 \equiv 1 \pmod{3}$. The inverse of 2 modulo 3 is 2, so $y_1 = 2$.
- **For $i=2$**: $M_2 = 105/5 = 21$. We need $y_2$ such that $21 y_2 \equiv 1 \pmod{5}$.
  Since $21 \equiv 1 \pmod{5}$, we solve $y_2 \equiv 1 \pmod{5}$. Thus $y_2 = 1$.
- **For $i=3$**: $M_3 = 105/7 = 15$. We need $y_3$ such that $15 y_3 \equiv 1 \pmod{7}$.
  Since $15 \equiv 1 \pmod{7}$, we solve $y_3 \equiv 1 \pmod{7}$. Thus $y_3 = 1$.

Now, construct $x$:

$$
x = a_1 M_1 y_1 + a_2 M_2 y_2 + a_3 M_3 y_3
$$

$$
x = (2 \times 35 \times 2) + (3 \times 21 \times 1) + (2 \times 15 \times 1)
$$

$$
x = 140 + 63 + 30 = 233
$$

Finally, we reduce modulo $M = 105$:

$$
233 \equiv 23 \pmod{105}
$$

So, $x \equiv 23 \pmod{105}$. 
The bag could contain 23, 128, 233... coins. The smallest positive number is 23.
