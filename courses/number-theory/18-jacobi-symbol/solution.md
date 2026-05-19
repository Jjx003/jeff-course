# Solution Walkthrough

The Jacobi symbol can be computed by repeatedly applying three rules:

1. Reduce the numerator: $\left(\frac{a}{n}\right)=\left(\frac{a\bmod n}{n}\right)$.
2. Pull out factors of $2$ using

$$
\left(\frac{2}{n}\right)=
\begin{cases}
1 & n\equiv 1,7 \pmod 8,\\
-1 & n\equiv 3,5 \pmod 8.
\end{cases}
$$

3. Apply quadratic reciprocity. Swapping odd `a` and `n` flips the sign exactly when both are $3 \pmod 4$.

The loop keeps a running `result` sign. After factors of `2` are removed, the swap `a, n = n, a` makes the numerator smaller after `a = a % n`, so the algorithm terminates quickly.

If the final denominator is `1`, the accumulated sign is the Jacobi symbol. Otherwise the inputs were not coprime, and the symbol is `0`.
