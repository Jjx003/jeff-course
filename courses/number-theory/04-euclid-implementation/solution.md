# Solution Walkthrough

The Euclidean algorithm rests on the lemma

$$
\gcd(a,b)=\gcd(b,a\bmod b).
$$

Each loop replaces the pair $(a,b)$ by the smaller pair $(b,a \bmod b)$. The second coordinate strictly decreases until it reaches $0$, so the algorithm terminates.

```python
while b != 0:
    a, b = b, a % b
return a
```

When $b=0$, every common divisor of $a$ and $0$ divides $a$, and the greatest one is $|a|$. The test cases use nonnegative inputs, so returning `a` matches the expected output.

The important implementation detail is the simultaneous assignment. Python evaluates the right side first, so `a % b` is computed using the old values before `a` and `b` are replaced.
