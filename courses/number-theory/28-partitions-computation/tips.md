### Hints
- **Base Case:** Remember that $p(0) = 1$ and $p(n) = 0$ for $n < 0$.
- **Memoization:** Since the recurrence depends on previous values, use an array to store $p(0), p(1), \dots, p(n)$ as you compute them.
- **Generating $g_k$:** You can generate the generalized pentagonal numbers on the fly or precompute them. The sequence starts $1, 2, 5, 7, 12, 15, \dots$.
- **Stopping Condition:** For a given $n$, only include terms $p(n - g_k)$ where $n - g_k \ge 0$.

### Going Deeper
- How does the performance of this recurrence compare to the standard dynamic programming approach (using parts of size $1, 2, \dots, n$)?
- The standard DP approach takes $O(n^2)$ time, whereas this recurrence takes $O(n \sqrt{n})$ because there are only about $\sqrt{8n/3}$ pentagonal numbers less than $n$.
