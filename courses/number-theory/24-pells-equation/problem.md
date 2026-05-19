# Pell's Equation

A **Diophantine equation** is an algebraic equation where we are strictly interested in integer solutions. One of the most famous non-linear Diophantine equations is **Pell's equation**, which has the form:

$$ x^2 - D y^2 = 1 $$

where $D$ is a given positive non-square integer, and we want to find integer solutions for $x$ and $y$. 

If $D$ is a perfect square, say $D = a^2$, the equation becomes $x^2 - a^2y^2 = 1 \implies (x - ay)(x + ay) = 1$. The only integer solutions to this are $x = \pm 1$ and $y = 0$, which are trivial.

However, if $D$ is **not a perfect square**, Pell's equation has *infinitely many* positive integer solutions. In this reading, we will explore the elegant structure of these solutions and how they are inextricably linked to the continued fraction expansion of $\sqrt{D}$.

### What's Next?
In the theory section, we'll formalize the connection between convergents of $\sqrt{D}$ and the solutions to this historic equation.