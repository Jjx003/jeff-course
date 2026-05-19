# Integer Partitions

In number theory and combinatorics, a **partition** of a positive integer $n$ is a way of writing $n$ as a sum of positive integers. Two sums that differ only in the order of their summands are considered the same partition.

For example, the integer $4$ can be partitioned in $5$ distinct ways:
- $4$
- $3 + 1$
- $2 + 2$
- $2 + 1 + 1$
- $1 + 1 + 1 + 1$

The **partition function** $p(n)$ represents the number of possible partitions of a non-negative integer $n$. By convention, $p(0) = 1$ (the empty sum), and $p(n) = 0$ for negative $n$. From the example above, $p(4) = 5$.

Unlike functions we've seen so far, there is no simple closed-form algebraic formula for $p(n)$. The values of $p(n)$ grow very quickly: $p(10) = 42$, $p(100) = 190,569,292$, and $p(1000)$ has $32$ digits.

So how do we compute $p(n)$ or reason about its properties? The most elegant way is through the use of **generating functions**, a powerful algebraic tool that translates combinatorial problems into polynomial algebra.

### What's Next?
In the theory section, we'll construct the generating function for $p(n)$ and uncover Euler's remarkable Pentagonal Number Theorem, which gives us a fast recursive way to compute partitions.