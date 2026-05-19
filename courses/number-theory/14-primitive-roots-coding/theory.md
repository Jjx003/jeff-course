# Implementation Theory

For a prime $p$, a primitive root modulo $p$ is an element $g$ whose powers generate every nonzero residue modulo $p$.

Equivalently, the order of $g$ modulo $p$ is exactly $p-1$.

**Criterion:** Let $q$ run over the distinct prime divisors of $p-1$. Then $g$ is a primitive root modulo $p$ if and only if

$$
g^{(p-1)/q}\not\equiv 1 \pmod p
$$

for every such $q$.

**Proof idea:** The order of $g$ must divide $p-1$. If the order is smaller than $p-1$, then it divides $(p-1)/q$ for at least one prime factor $q$ of $p-1$, causing the corresponding power to be $1$.

The implementation therefore factors $p-1$ once, then tests candidates $g=2,3,\ldots$ until the criterion succeeds.
