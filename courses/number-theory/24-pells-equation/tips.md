### Recap

- **Pell's equation** $x^2 - Dy^2 = 1$ has infinitely many solutions for any non-square $D > 0$.
- All solutions can be found among the **convergents** of the continued fraction of $\sqrt{D}$.
- The **fundamental solution** $(x_1, y_1)$ occurs just before the end of the first period (if the period length $m$ is even) or the second period (if $m$ is odd).
- Every other solution can be generated using powers of $(x_1 + y_1\sqrt{D})$.

### Historical Note

Although named after John Pell by Euler, Pell had little to do with the equation! It was extensively studied by Indian mathematicians centuries earlier. Brahmagupta (in 628 CE) developed the *chakravala* method to solve it, and Bhaskara II found the solution for $D=61$ in the 12th century, long before Fermat posed it as a challenge in Europe.

[Next up, let's write an algorithm to find these fundamental solutions!](/tracks/number-theory/problems/pells-equation-solver)