# Hensel's Lemma

Solving polynomial equations over the integers, like $x^2 \equiv a \pmod m$, is a common task in number theory and cryptography. 

If we can factor $m$ into its prime factorization $m = p_1^{k_1} p_2^{k_2} \cdots p_r^{k_r}$, we can use the Chinese Remainder Theorem to break the problem down into solving $x^2 \equiv a \pmod{p_i^{k_i}}$ for each prime power, and then combine the results.

But how do we solve a polynomial congruence modulo a prime power like $p^k$? 

We usually start by finding the solutions modulo the prime $p$. Then, we use an incredible technique called **Hensel's Lemma** to "lift" these solutions to modulo $p^2$, then $p^3$, and all the way up to $p^k$. 

In this module, we will explore Hensel's Lemma, which you can think of as the number-theoretic equivalent of Newton's method for finding roots in calculus!

---

### Recap

Solving congruences modulo composites is typically done by breaking the problem down using the Chinese Remainder Theorem, then applying Hensel's Lemma to lift roots modulo primes to roots modulo prime powers.

[Next up: Testing your knowledge in the Hensel's Lemma Quiz](/tracks/number-theory/problems/hensels-lemma-quiz)
