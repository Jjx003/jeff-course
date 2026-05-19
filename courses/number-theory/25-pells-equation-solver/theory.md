# Implementation Theory

Pell's equation

$$
x^2-Dy^2=1
$$

is solved by the convergents of the continued fraction for $\sqrt D$.

For nonsquare $D$, the continued fraction of $\sqrt D$ is periodic. Its convergents

$$
\frac{h_k}{k_k}
$$

give increasingly accurate rational approximations to $\sqrt D$. The first convergent satisfying

$$
h_k^2-Dk_k^2=1
$$

is the minimal positive solution.

The recurrence variables `m`, `d_val`, and `a` generate the periodic continued fraction terms for $\sqrt D$. The variables `h_prev`, `h_curr`, `k_prev`, and `k_curr` maintain consecutive convergent numerators and denominators.
