# Solving Pell's Equation

Your task is to write an algorithm that finds the fundamental solution to Pell's equation:

$$
x^2 - D y^2 = 1
$$

Here $D$ is a positive non-square integer. The **fundamental solution** is the positive solution $(x_1, y_1)$ with the smallest possible $x_1$.

As we learned in the previous reading, the fundamental solution can be found by computing convergents of the continued fraction expansion of $\sqrt{D}$.

### The Algorithm

First generate the continued fraction coefficients for $\sqrt{D}$. Start with

$$
m_0 = 0, \qquad d_0 = 1, \qquad a_0 = \lfloor \sqrt{D} \rfloor.
$$

Then repeat the exact integer recurrence

$$
m_{n+1} = d_n a_n - m_n,
$$

$$
d_{n+1} = \frac{D - m_{n+1}^2}{d_n},
$$

$$
a_{n+1} = \left\lfloor \frac{a_0 + m_{n+1}}{d_{n+1}} \right\rfloor.
$$

Next compute the convergents $p_n / q_n$. Use the initial values

$$
p_{-2} = 0, \qquad p_{-1} = 1,
$$

$$
q_{-2} = 1, \qquad q_{-1} = 0,
$$

and update with

$$
p_n = a_n p_{n-1} + p_{n-2},
$$

$$
q_n = a_n q_{n-1} + q_{n-2}.
$$

After each convergent, check whether it solves Pell's equation:

$$
p_n^2 - D q_n^2 = 1.
$$

The first convergent that satisfies this equation is the fundamental solution $(x_1, y_1) = (p_n, q_n)$.

### Implementation Details

Write a function `solve_pell(D)` that returns a tuple `(x, y)` representing the fundamental solution. The starter code includes test cases. For values like $D = 61$ or $D = 109$, the solutions are large, but Python integers have arbitrary precision, so you do not need special overflow handling.
