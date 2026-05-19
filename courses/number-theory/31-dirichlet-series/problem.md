# Dirichlet Series and Arithmetic Functions

As we conclude this course, we reach one of the most powerful bridges in all of mathematics: the connection between **arithmetic functions** (discrete) and **Dirichlet series** (analytic). This bridge allows us to use the tools of complex analysis to probe the distribution of prime numbers.

## Arithmetic Functions and Convolution

An **arithmetic function** is any function $f: \mathbb{N} \to \mathbb{C}$. We've encountered many already:

- $\mu(n)$: The Mobius function.
- $\phi(n)$: Euler's totient function.
- $d(n)$: The number of divisors of $n$.
- $\sigma(n)$: The sum of divisors of $n$.

The natural "product" for these functions is not pointwise multiplication, but **Dirichlet convolution**, denoted by $(f * g)$:

$$
(f * g)(n) = \sum_{d|n} f(d)g(n/d)
$$

This operation is commutative and associative. The identity element is the function $\epsilon(n)$:

$$
\epsilon(n) =
\begin{cases}
1 & \text{if } n = 1, \\
0 & \text{if } n > 1.
\end{cases}
$$

## Dirichlet Series

A **Dirichlet series** is a series of the form:

$$
F(s) = \sum_{n=1}^{\infty} \frac{f(n)}{n^s}
$$

where $s = \sigma + it$ is a complex variable. The most famous example is the **Riemann zeta function**, where $f(n) = 1$ for all $n$:

$$
\zeta(s) = \sum_{n=1}^{\infty} \frac{1}{n^s}
$$

The key algebraic fact is that Dirichlet series turn convolution into multiplication. If $F(s)$ is the series for $f$ and $G(s)$ is the series for $g$, then, where the products converge absolutely,

$$
\begin{aligned}
F(s)G(s)
&= \left( \sum_{n=1}^{\infty} \frac{f(n)}{n^s} \right)
   \left( \sum_{m=1}^{\infty} \frac{g(m)}{m^s} \right) \\
&= \sum_{k=1}^{\infty} \frac{(f * g)(k)}{k^s}.
\end{aligned}
$$

## Euler Products

For **multiplicative** arithmetic functions ($f(mn) = f(m)f(n)$ whenever $\gcd(m,n)=1$), the Dirichlet series can be written as an infinite product over primes:

$$
\sum_{n=1}^{\infty} \frac{f(n)}{n^s}
= \prod_{p \text{ prime}}
\left( 1 + \frac{f(p)}{p^s} + \frac{f(p^2)}{p^{2s}} + \dots \right)
$$

For the zeta function, this yields the celebrated **Euler product formula**:

$$
\zeta(s) = \prod_{p} \left( 1 - p^{-s} \right)^{-1}
$$

This formula is the analytic statement of the **Fundamental Theorem of Arithmetic**.
