### Debugging Hints

- The terms $d_k$ will always evenly divide $D - m_{k+1}^2$. Use integer division `//` in Python to keep all variables as exact integers.
- Be careful with the initial values of the convergent recurrence. Before your loop, you can initialize $p_{-2} = 0$, $p_{-1} = 1$, $q_{-2} = 1$, and $q_{-1} = 0$, then apply the recurrence directly inside the loop starting with $a_0$.
- Alternatively, you can pre-calculate $p_0 = a_0$ and $q_0 = 1$ and start the loop at the next continued-fraction coefficient.
- Remember that $a_0 = \lfloor\sqrt{D}\rfloor$. You can use `math.isqrt(D)` to get this exactly without floating-point precision issues.

### Mathematical Insight
Why does `math.isqrt(D)` avoid precision issues? For very large $D$, floating-point `int(math.sqrt(D))` can lose the lower bits of precision, resulting in an incorrect integer part. `math.isqrt` uses exact integer arithmetic internally.
