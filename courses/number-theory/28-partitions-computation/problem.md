# Computing Partitions

The partition function $p(n)$ counts the number of ways to write $n$ as a sum of positive integers. While simple to define, $p(n)$ grows extremely fast. A naive recursive approach would be far too slow for even moderate values of $n$.

In this exercise, you will implement an efficient algorithm to compute $p(n)$ using **Euler's Pentagonal Number recurrence**:

$$ p(n) = \sum_{k \neq 0} (-1)^{k-1} p(n - g_k) $$

where $g_k = \frac{k(3k-1)}{2}$ are the generalized pentagonal numbers ($k = 1, -1, 2, -2, 3, -3, \dots$).

### Task
Implement a function `partition_function(n)` that returns the value of $p(n)$.

### Constraints
- $0 \le n \le 500$
- Your solution should run in $O(n \sqrt{n})$ time.

### Example
```python
>>> partition_function(5)
7
>>> partition_function(10)
42
>>> partition_function(100)
190569292
```
