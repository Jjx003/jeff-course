### Recap

- A **partition** of $n$ is a sum of positive integers that add up to $n$ (order doesn't matter).
- The generating function for partitions is $\prod_{k=1}^{\infty} \frac{1}{1-x^k}$.
- Euler's **Pentagonal Number Theorem** expands the inverse of the generating function.
- This gives a fast $O(n \sqrt{n})$ dynamic programming recurrence to compute $p(n)$ using generalized pentagonal numbers.

### Combinatorial Proof
Euler proved his pentagonal number theorem algebraically, but a famous combinatorial proof was found by Franklin in 1881. He demonstrated a near-perfect bijection between partitions of $n$ into an *even* number of distinct parts and partitions into an *odd* number of distinct parts. The bijection only fails when the parts form certain "pentagonal" shapes, leaving exactly an excess of $+1$ or $-1$.

[In the next modules, we'll see how to write code to compute the partition function efficiently.](/tracks/number-theory/problems/partitions-quiz)