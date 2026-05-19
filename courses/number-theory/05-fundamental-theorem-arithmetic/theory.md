# Primes and the Fundamental Theorem

## Prime Numbers

An integer $p > 1$ is called a **prime number** if its only positive divisors are $1$ and $p$. An integer $n > 1$ that is not prime is called **composite**. 

![Prime Distribution](/courses/number-theory/prime-distribution.svg)

If $n$ is composite, there exist integers $a$ and $b$ such that $n = a \cdot b$, where $1 < a < n$ and $1 < b < n$.

### Euclid's Proof of Infinite Primes

One of the oldest and most beautiful proofs in mathematics is Euclid's proof that there are infinitely many primes. The proof proceeds by contradiction.

**Theorem:** There are infinitely many prime numbers.

**Proof:**

Assume, for the sake of contradiction, that there are only finitely many prime numbers. We can list them all as $p_1, p_2, \ldots, p_k$. 

Consider the integer $N$ constructed by multiplying all these primes together and adding 1:

$$
N = p_1 \cdot p_2 \cdots p_k + 1
$$

Since $N > p_k$, the number $N$ itself is not in our list of all primes. Whether $N$ is prime or composite, it has a prime divisor.

Let $p_i$ be a prime that divides $N$. Because $p_i$ is in our complete list of primes, $p_i$ also divides the product $p_1 \cdot p_2 \cdots p_k$.

If $p_i$ divides both $N$ and $p_1 \cdot p_2 \cdots p_k$, it must divide their difference:

$$
N - (p_1 \cdot p_2 \cdots p_k) = 1
$$

This implies that $p_i$ divides 1, which is impossible since $p_i \ge 2$. This contradiction means our initial assumption, that the number of primes is finite, must be false. Therefore, there are infinitely many primes. $\blacksquare$

## Euclid's Lemma

Before we can prove the unique factorization of integers, we need a crucial stepping stone known as Euclid's Lemma, which relies on the greatest common divisor properties you learned earlier.

**Theorem (Euclid's Lemma):** If a prime $p$ divides a product $ab$, then $p$ divides $a$ or $p$ divides $b$.

**Proof:**

Suppose $p \mid ab$ but $p \nmid a$. Since $p$ is prime, its only positive divisors are $1$ and $p$. Since $p$ does not divide $a$, the greatest common divisor of $p$ and $a$ must be 1, i.e., $\gcd(a, p) = 1$.

By Bezout's Identity, there exist integers $x$ and $y$ such that:

$$
ax + py = 1
$$

Multiply the entire equation by $b$:

$$
abx + pby = b
$$

We know that $p$ divides $ab$, so we can write $ab = pk$ for some integer $k$. Substituting this into our equation gives:

$$
p(kx) + p(by) = b
$$

$$
p(kx + by) = b
$$

Since $kx + by$ is an integer, this shows that $p \mid b$. Thus, if $p \nmid a$, then $p \mid b$. $\blacksquare$

## The Fundamental Theorem of Arithmetic

We now arrive at the central theorem of this module.

**Theorem:** Every integer $n > 1$ can be represented as a product of prime numbers in exactly one way, apart from the order of the factors.

**Proof of Existence:**

We proceed by strong induction on $n$.

Base case: $n = 2$ is prime, so it is its own prime factorization.

Inductive step: Assume that every integer $k$ such that $2 \le k < n$ can be factored into primes. If $n$ is prime, we are done. If $n$ is composite, it can be written as $n = a \cdot b$, where $1 < a, b < n$. By our inductive hypothesis, both $a$ and $b$ can be factored into primes. Multiplying their factorizations yields a prime factorization for $n$.

**Proof of Uniqueness:**

Suppose an integer $n$ has two different prime factorizations:

$$
n = p_1 p_2 \cdots p_r = q_1 q_2 \cdots q_s
$$

where the $p_i$ and $q_j$ are prime. We can assume the primes are sorted such that $p_1 \le p_2 \le \ldots \le p_r$ and $q_1 \le q_2 \le \ldots \le q_s$.

Since $p_1$ divides $n$, it must divide the product $q_1 q_2 \cdots q_s$. By repeatedly applying Euclid's Lemma, $p_1$ must divide at least one of the $q_j$. Since $q_j$ is prime, $p_1 = q_j$.

We can divide both sides of the equation by this common prime factor. We repeat this process. If $r \neq s$, we would eventually be left with $1$ on one side and a product of primes on the other, which is impossible. Thus, $r = s$. Moreover, since we assumed the primes were sorted, each $p_i$ must pair exactly with $q_i$. The factorization is unique. $\blacksquare$

## Looking Ahead

Because factorization is unique, primes uniquely define numbers. In the upcoming coding module, you will put this theory into practice by implementing the **Sieve of Eratosthenes** to efficiently find all primes up to a given limit, and you will write an algorithm to compute the unique prime factorization of any integer.
