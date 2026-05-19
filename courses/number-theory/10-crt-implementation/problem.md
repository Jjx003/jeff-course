# Chinese Remainder Theorem Implementation

In the previous module, we learned the constructive proof for the Chinese Remainder Theorem. Now it's time to turn that math into code.

Your task is to write a function `solve_crt(remainders, moduli)` that takes two lists of integers of the same length:
1. `remainders`: A list of the remainders ($a_i$).
2. `moduli`: A list of the corresponding moduli ($m_i$).

The function should return the smallest non-negative integer $x$ that satisfies the system of congruences:

$$
x \equiv a_i \pmod{m_i} \quad \text{for all } i
$$

You are guaranteed that all moduli are strictly greater than 1, and that they are pairwise coprime.

### Example

```python
remainders = [2, 3, 2]
moduli = [3, 5, 7]
# solve_crt(remainders, moduli) should return 23
```

### Constraints
- $1 \le \text{length of lists} \le 10$
- $2 \le m_i \le 10^5$
- $0 \le a_i < m_i$
- The product of all moduli will fit within standard integer types (no overflow issues in Python).
