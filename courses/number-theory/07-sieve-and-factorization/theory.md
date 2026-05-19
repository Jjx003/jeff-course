# Primes and Factorization

Prime numbers are the "atoms" of the integers. Because every integer is uniquely constructed by multiplying primes together, understanding the structure of numbers requires us to identify primes and prime factorizations.

## Trial Division for Factorization

How can we find the prime factors of a number $n$? The simplest method is **trial division**. We simply test if $n$ is divisible by $2, 3, 4, \dots$ and divide it out whenever we find a factor.

An important optimization makes this efficient: **we only need to test divisors up to $\sqrt{n}$.** If $n$ has a factor $d$ greater than $\sqrt{n}$, the corresponding factor $n/d$ must be less than $\sqrt{n}$. 

If we have tested all numbers up to $\sqrt{n}$ and found no factors, then $n$ itself must be prime! This is extremely powerful. Factoring $10^{12}$ requires at most $10^6$ divisions, which takes a computer only a fraction of a second.

## The Sieve of Eratosthenes

What if we want to generate *all* primes up to $N$? We could run trial division on every number from $1$ to $N$, but there is a much faster algorithm attributed to the ancient Greek mathematician Eratosthenes.

Instead of testing each number for primality, the **Sieve of Eratosthenes** works by assuming all numbers are prime, and then systematically crossing out the multiples of known primes.

| 2 | 3 | ~~4~~ | 5 | ~~6~~ | 7 | ~~8~~ | ~~9~~ | ~~10~~ |
|---|---|---|---|---|---|---|---|---|
| 11 | ~~12~~ | 13 | ~~14~~ | ~~15~~ | ~~16~~ | 17 | ~~18~~ | 19 |
| ~~20~~ | ~~21~~ | ~~22~~ | 23 | ~~24~~ | ~~25~~ | ~~26~~ | ~~27~~ | ~~28~~ |

1. Create a boolean array `is_prime` of size $N+1$, initialized to `True`. Set `is_prime[0]` and `is_prime[1]` to `False`.
2. Loop $p$ from $2$ to $\sqrt{N}$.
3. If `is_prime[p]` is `True`, it is a prime. We then iterate through all multiples of $p$ ($p^2, p^2+p, p^2+2p, \dots$) up to $N$ and mark them as `False`.
4. After the loop finishes, the indices of the array that still hold `True` are exactly the prime numbers up to $N$.

Notice that we can start crossing out multiples at $p^2$, because any smaller multiple of $p$ (e.g., $p \cdot 2, p \cdot 3$) would have already been crossed out by a smaller prime factor!
