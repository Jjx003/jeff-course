We've spent considerable time understanding equations of one variable, particularly quadratic congruences like $x^2 \equiv a \pmod p$. But what happens when we look at polynomials with *two* variables?

A **binary quadratic form** is a homogeneous polynomial of degree 2 in two variables, $x$ and $y$:

$$ f(x, y) = ax^2 + bxy + cy^2 $$

where $a, b, c$ are integers. We often abbreviate this form as $(a, b, c)$.

### The Central Question

Given a specific binary quadratic form $f$, which integers $n$ can be represented by it? That is, for which $n$ do there exist integers $x$ and $y$ such that:

$$ ax^2 + bxy + cy^2 = n $$

This question generalize many famous problems in number theory:
1. **Sums of squares:** Which numbers are of the form $x^2 + y^2$? (Here $a=1, b=0, c=1$).
2. **Pell's equation:** $x^2 - dy^2 = 1$. (Here $a=1, b=0, c=-d$).

In this module, we will explore the theory developed by Fermat, Euler, Lagrange, and Gauss to systematically answer these questions. We will focus on the **discriminant** of a form, the notion of **equivalence** between forms, and **reduction** of positive definite forms.
