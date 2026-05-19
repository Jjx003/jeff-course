## The Algebraic Structure of Arithmetic Functions

Let $\mathbb{A}$ be the set of all arithmetic functions $f: \mathbb{N} \to \mathbb{C}$ such that $f(1) \neq 0$. We will show that $(\mathbb{A}, *, \epsilon)$ forms an abelian group.

### 1. Commutativity

$$
\begin{aligned}
(f * g)(n)
&= \sum_{d|n} f(d)g(n/d) \\
&= \sum_{ab=n} f(a)g(b) \\
&= \sum_{ba=n} g(b)f(a)
= (g * f)(n).
\end{aligned}
$$

### 2. Associativity

$$
((f * g) * h)(n)
= \sum_{abc=n} f(a)g(b)h(c)
= (f * (g * h))(n)
$$

### 3. Identity

By definition, $(\epsilon * f)(n) = \sum_{d|n} \epsilon(d)f(n/d)$. Since $\epsilon(d) = 0$ for $d > 1$, the only non-zero term is for $d=1$, which gives $1 \cdot f(n/1) = f(n)$.

### 4. Inverses

For any $f$ with $f(1) \neq 0$, we define $f^{-1}$ recursively:

$$
f^{-1}(1) = \frac{1}{f(1)}
$$

$$
f^{-1}(n) =
\frac{-1}{f(1)} \sum_{\substack{d|n \\ d > 1}} f(d)f^{-1}(n/d)
$$

This ensures $(f * f^{-1})(n) = \epsilon(n)$.

---

## Euler Product Proof

**Theorem:** If $f$ is multiplicative and $\sum |f(n)|n^{-\sigma}$ converges, then:

$$
\sum_{n=1}^{\infty} \frac{f(n)}{n^s}
= \prod_{p} \sum_{k=0}^{\infty} \frac{f(p^k)}{p^{ks}}
$$

**Proof Strategy:**

Consider the finite product over primes $p \le X$:

$$
P(X) = \prod_{p \le X}
\left( 1 + \frac{f(p)}{p^s} + \frac{f(p^2)}{p^{2s}} + \dots \right)
$$

By the Fundamental Theorem of Arithmetic, every $n$ whose prime factors are all $\le X$ appears exactly once in the expansion of $P(X)$:

$$
P(X) = \sum_{n \in S_X} \frac{f(n)}{n^s}
$$

where $S_X$ is the set of integers whose prime factors are $\le X$. As $X \to \infty$, $S_X$ exhausts $\mathbb{N}$. Since the series converges absolutely, the limit exists and equals the Dirichlet series.

---

## Generating Functions for Classics

Using the property $(f * g) \leftrightarrow F(s)G(s)$, we can derive:

1. **Mobius Inversion:** Since $\mu * \mathbf{1} = \epsilon$, where $\mathbf{1}(n)=1$:

$$
\frac{1}{\zeta(s)} = \sum_{n=1}^{\infty} \frac{\mu(n)}{n^s}
$$

2. **Divisor Function:** $d = \mathbf{1} * \mathbf{1}$

$$
\zeta(s)^2 = \sum_{n=1}^{\infty} \frac{d(n)}{n^s}
$$

3. **Euler Totient:** $\phi = \mu * \text{Id}$, where $\text{Id}(n)=n$:

$$
\frac{\zeta(s-1)}{\zeta(s)} = \sum_{n=1}^{\infty} \frac{\phi(n)}{n^s}
$$
