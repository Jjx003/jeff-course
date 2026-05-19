# Prime Factorization and Sieve

A **prime number** is an integer greater than 1 that has no positive divisors other than 1 and itself. The fundamental theorem of arithmetic states that every integer greater than 1 is either a prime itself or can be uniquely factored into a product of primes.

There are two common tasks when dealing with prime numbers:
1. Factoring a specific number into its prime components.
2. Generating all prime numbers up to a given limit $N$.

## The Problem

You need to implement two functions:

1. `prime_factors(n)`: Given an integer $n \ge 2$, return a sorted list of its prime factors. If a prime factor appears multiple times, it should appear that many times in the list. For example, `prime_factors(12)` should return `[2, 2, 3]`.
2. `sieve_of_eratosthenes(limit)`: Given an integer $limit \ge 2$, return a list of all prime numbers less than or equal to `limit`. Implement this using the Sieve of Eratosthenes algorithm for efficiency.

### Constraints
- For factorization: $2 \le n \le 10^{12}$
- For the sieve: $2 \le limit \le 10^6$

### Expected Output

Your program will test both functions and print their outputs.
