# Implementation Theory

Pell's equation

$$
x^2 - D y^2 = 1
$$

is solved by the convergents of the continued fraction for $\sqrt{D}$.

For nonsquare $D$, the continued fraction for $\sqrt{D}$ is eventually periodic; in fact it is purely periodic after the initial term:

$$
\sqrt{D} = [a_0; \overline{a_1, a_2, \ldots, a_\ell}].
$$

Its convergents

$$
\frac{p_n}{q_n}
$$

give especially good rational approximations to $\sqrt{D}$. Pell's equation asks for an approximation so good that

$$
p_n^2 - D q_n^2 = 1.
$$

The continued-fraction recurrence does all work with integers:

$$
\begin{aligned}
m_{n+1} &= d_n a_n - m_n, \\
d_{n+1} &= \frac{D - m_{n+1}^2}{d_n}, \\
a_{n+1} &= \left\lfloor \frac{a_0 + m_{n+1}}{d_{n+1}} \right\rfloor.
\end{aligned}
$$

These variables encode the exact identity

$$
\frac{\sqrt{D} + m_n}{d_n} = [a_n; a_{n+1}, a_{n+2}, \ldots],
$$

so no floating-point arithmetic is needed after computing $a_0 = \lfloor \sqrt{D} \rfloor$.

Maintain consecutive convergent numerators and denominators with

$$
\begin{aligned}
p_n &= a_n p_{n-1} + p_{n-2}, \\
q_n &= a_n q_{n-1} + q_{n-2}.
\end{aligned}
$$

The first convergent for which $p_n^2 - Dq_n^2 = 1$ is the minimal positive solution. The previous reading explains why every positive Pell solution must appear among these convergents.
