# Solution Walkthrough

The helper `get_prime_factors` returns the distinct prime factors of $p-1$. Distinct factors are enough because the primitive-root test only needs to check one exponent for each prime divisor.

For each candidate `g`, test:

```python
pow(g, phi // q, p) == 1
```

If this happens for any prime factor `q` of `phi = p - 1`, then `g` has order smaller than `phi`, so it cannot be primitive.

If no test returns `1`, the order of `g` must be exactly `p-1`, and `g` is a primitive root. Because the loop tries candidates in increasing order, the first success is the smallest primitive root.
