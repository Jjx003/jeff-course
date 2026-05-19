# Tips

1. **Factorization:** First, find all unique prime factors of $p-1$. You can modify the trial division algorithm we used previously. Since you only need the unique prime factors, you don't need to keep their multiplicities.
2. **Fast Exponentiation:** Use the built-in `pow(base, exp, mod)` function in Python, which is much faster than computing `(base ** exp) % mod` manually.
3. **Linear Search:** Start testing candidates $g$ from 2 upwards. For each $g$, check the condition $g^{(p-1)/q} \not\equiv 1 \pmod p$ for all prime factors $q$ of $p-1$. The first $g$ that satisfies this for *all* prime factors is the smallest primitive root.
4. **Why it's fast:** The smallest primitive root is usually very small (often 2, 3, or 5). The search will terminate quickly.