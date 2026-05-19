## The Generating Function for $p(n)$

A **generating function** encodes an infinite sequence of numbers as the coefficients of a formal power series. For the partition function $p(n)$, the generating function is:

$$
P(x) = \sum_{n=0}^{\infty} p(n)x^n = 1 + x + 2x^2 + 3x^3 + 5x^4 + 7x^5 + \dots
$$

A common way to visualize a partition is through a **Young diagram** (or Ferrers diagram). Each number in the partition is represented by a row of boxes. For example, the partition $5 + 3 + 2 = 10$ is shown below:

![Young Diagram](/courses/number-theory/young-diagram.svg)

The number of partitions $p(n)$ grows extremely rapidly as $n$ increases. 

![Partition Growth](/courses/number-theory/partition-growth.svg)

Euler discovered that we can write this infinite series as an infinite product. To form a partition of $n$, we can pick any number of $1$'s, any number of $2$'s, any number of $3$'s, and so on. We can represent the choice of $k$'s with the geometric series $1 + x^k + x^{2k} + x^{3k} + \dots = \frac{1}{1 - x^k}$.

Multiplying these series together for all $k \ge 1$ gives the generating function:

$$
\sum_{n=0}^{\infty} p(n)x^n = \prod_{k=1}^{\infty} \frac{1}{1 - x^k}
$$

When we expand this infinite product, the coefficient of $x^n$ is exactly the number of ways to pick terms whose exponents sum to $n$, which perfectly models integer partitions!

## Euler's Pentagonal Number Theorem

While the generating function is conceptually beautiful, calculating its coefficients directly from the infinite fraction is tedious. Euler noticed something miraculous when he expanded the *denominator* of the product:

$$
\prod_{k=1}^{\infty} (1 - x^k) = 1 - x - x^2 + x^5 + x^7 - x^{12} - x^{15} + \dots
$$

The non-zero coefficients are only $+1$ or $-1$, and the powers of $x$ follow a specific sequence: $1, 2, 5, 7, 12, 15 \dots$

These exponents are the **generalized pentagonal numbers**. The $m$-th generalized pentagonal number is given by the formula:

$$
g_m = \frac{m(3m - 1)}{2}
$$

for integers $m = 1, -1, 2, -2, 3, -3 \dots$ 

This expansion leads to **Euler's Pentagonal Number Theorem**:

$$
\prod_{k=1}^{\infty} (1 - x^k) = \sum_{m=-\infty}^{\infty} (-1)^m x^{m(3m-1)/2}
$$

## A Fast Recurrence Relation

Because $P(x)$ and the infinite product are inverses, we have:

$$
\left( \sum_{n=0}^{\infty} p(n)x^n \right)
\left( \sum_{m=-\infty}^{\infty} (-1)^m x^{g_m} \right) = 1
$$

By equating the coefficient of $x^n$ (for $n > 0$) to zero on both sides, we get a recurrence relation for $p(n)$:

$$
p(n) - p(n-1) - p(n-2) + p(n-5) + p(n-7) - p(n-12) - p(n-15) + \dots = 0
$$

Rearranging this gives a formula to compute $p(n)$:

$$
p(n) = \sum_{j=1}^{\infty} (-1)^{j-1}
\left(p(n - g_j) + p(n - g_{-j})\right)
$$

where $g_j = j(3j-1)/2$ and $g_{-j} = j(3j+1)/2$. This is what creates the sign pattern $+,+,-,-,+,+,\dots$. The sum stops once both pentagonal numbers exceed $n$ because $p(\text{negative}) = 0$.

This recurrence reduces the complexity of computing $p(n)$ dramatically. Instead of generating all partitions, we only need to look back at $O(\sqrt{n})$ previous values of the partition function!
