# Study Tips & Recap

### Recap

- **GCD:** The greatest integer $d$ that divides both $a$ and $b$.
- **The Core Lemma:** $\gcd(a, b) = \gcd(b, a \bmod b)$. This effectively lets us "shrink" the problem.
- **Euclidean Algorithm:** Repeatedly apply the division algorithm replacing $(a, b)$ with $(b, r)$ until $r=0$. The GCD is the last non-zero remainder.
- **Termination:** The algorithm terminates because remainders are strictly decreasing non-negative integers.

### Tips for Computing by Hand

When tracing the algorithm by hand, you only need to keep track of the $a$, $b$, and $r$ values at each step. The quotient $q$ is just a stepping stone to find $r$.
You can think of each step as:
$$ \text{new\_a} = \text{old\_b} $$
$$ \text{new\_b} = \text{old\_a} \bmod \text{old\_b} $$

### Going Deeper

In the next module, you will write code to implement this algorithm efficiently. While it takes only a few lines of code, understanding the rigorous proof behind *why* it works gives you the foundation to tackle more advanced topics like the Extended Euclidean Algorithm and modular inverses.