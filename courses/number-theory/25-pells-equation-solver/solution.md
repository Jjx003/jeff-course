# Solution Walkthrough

The solver starts by rejecting perfect squares. If $D$ is a square, then $x^2 - Dy^2 = 1$ factors as $(x-\sqrt{D}y)(x+\sqrt{D}y)=1$, so there is no positive solution with $y>0$ to find.

For nonsquare $D$, compute the continued fraction of $\sqrt D$:

```python
m = d_val * a - m
d_val = (D - m * m) // d_val
a = (a0 + m) // d_val
```

After each new coefficient `a`, update the convergent numerator and denominator:

```python
p_next = a * p_curr + p_prev
q_next = a * q_curr + q_prev
```

Then test whether the current convergent solves Pell's equation:

```python
p_curr * p_curr - D * q_curr * q_curr == 1
```

The first success is returned. Continued fraction theory guarantees that this first success is the minimal positive solution.
