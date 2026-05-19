# Solution Walkthrough

First multiply the moduli to get the combined period:

```python
M = 1
for m in moduli:
    M *= m
```

For each congruence $x \equiv a_i \pmod{m_i}$, compute `Mi = M // m_i`. This number is divisible by every other modulus, but not by `m_i`.

The modular inverse

```python
yi = pow(Mi, -1, m)
```

is the number satisfying `Mi * yi == 1 mod m`. So `a * Mi * yi` behaves like `a` modulo `m`, and behaves like `0` modulo every other modulus.

Summing those terms gives a solution to every congruence at once. Returning `x % M` selects the smallest nonnegative representative.
