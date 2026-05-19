# Solution Walkthrough

This exercise has two related routines: trial division for one integer, and the sieve for a whole range.

## Prime factorization

For `prime_factors(n)`, try possible divisors `d` starting at 2. Whenever `d` divides `n`, append it and divide it out:

```python
while n % d == 0:
    factors.append(d)
    n //= d
```

The loop only needs to continue while `d * d <= n`. If no divisor at most $\sqrt n$ remains, then the leftover `n` is either `1` or prime. That is why the final `if n > 1` appends the last prime factor.

## Sieve of Eratosthenes

The sieve begins by assuming every number is prime, then crosses out multiples of each discovered prime. Starting at `p * p` is enough because smaller multiples of `p` were already crossed out by smaller primes.

The final list comprehension returns every index still marked prime.
