# Solution Walkthrough

The solver starts by rejecting perfect squares. If $D$ is a square, then $x^2-Dy^2=1$ has no nontrivial Pell behavior.

For nonsquare $D$, compute the continued fraction of $\sqrt D$:

```python
m = d_val * a - m
d_val = (D - m * m) // d_val
a = (a0 + m) // d_val
```

After each new coefficient `a`, update the convergent:

```python
h_next = a * h_curr + h_prev
k_next = a * k_curr + k_prev
```

Then test whether the current convergent solves Pell's equation:

```python
h_curr * h_curr - D * k_curr * k_curr == 1
```

The first success is returned. Continued fraction theory guarantees that this first success is the minimal positive solution.
