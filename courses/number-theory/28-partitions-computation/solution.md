# Solution Walkthrough

The dynamic-programming array `p` stores already-computed partition values, with `p[0] = 1`.

For each target `i`, the code walks through generalized pentagonal numbers:

```python
g_pos = k * (3 * k - 1) // 2
g_neg = (-k) * (3 * (-k) - 1) // 2
```

These are $g_k$ and $g_{-k}$. If either one is at most `i`, add or subtract the corresponding earlier value.

The sign is positive for odd `k` and negative for even `k`, producing the pair pattern

$$
+,+,-,-,+,+,\ldots
$$

Once both pentagonal numbers are larger than `i`, no later term can contribute, so the inner loop stops. Returning `p[n]` gives the requested partition count.
