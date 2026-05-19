### The Discriminant

The most important invariant of a binary quadratic form $f(x, y) = ax^2 + bxy + cy^2$ is its **discriminant**, defined exactly as it is for the quadratic formula:

$$
\Delta = b^2 - 4ac
$$

The discriminant tells us fundamentally about the shape and behavior of the form. 

- If $\Delta > 0$ and is not a perfect square, the form is **indefinite** (it can take both positive and negative values).
- If $\Delta < 0$, the form is **definite**. Specifically, if $a > 0$, it is **positive definite** (it only takes positive values for $(x,y) \neq (0,0)$), and if $a < 0$, it is **negative definite**.

![Quadratic Form Surface](/courses/number-theory/quadratic-form.svg)

**Theorem:** The discriminant of an integral binary quadratic form is always congruent to $0$ or $1 \pmod 4$. This is because $b^2 \equiv 0$ or $1 \pmod 4$, and $4ac \equiv 0 \pmod 4$. Conversely, only integers congruent to $0$ or $1 \pmod 4$ can occur as such discriminants.

### Equivalence of Forms

Two forms might look different but represent the exact same set of integers. For example, $x^2 + y^2$ and $(x+y)^2 + y^2 = x^2 + 2xy + 2y^2$ clearly represent the same values, just with a substitution of variables.

We formalize this using matrices. A form $ax^2 + bxy + cy^2$ can be written as:

$$
\begin{pmatrix} x & y \end{pmatrix}
\begin{pmatrix} a & b/2 \\ b/2 & c \end{pmatrix}
\begin{pmatrix} x \\ y \end{pmatrix}
$$

Two forms $f$ and $g$ are **equivalent** (written $f \sim g$) if there is an invertible integer matrix $M = \begin{pmatrix} \alpha & \beta \\ \gamma & \delta \end{pmatrix}$ with determinant $+1$ such that:

$$
\begin{pmatrix} x \\ y \end{pmatrix}
= M
\begin{pmatrix} X \\ Y \end{pmatrix}
$$

transforms $f(x,y)$ into $g(X,Y)$. A key property is that equivalent forms have the **same discriminant** and represent the **same set of integers**.

### Reduced Forms

To understand all forms of a given discriminant $\Delta < 0$, Gauss introduced the idea of a **reduced form**. A positive definite form $(a, b, c)$ is reduced if:

$$
|b| \le a \le c
$$

And if $|b| = a$ or $a = c$, then $b \ge 0$.

**Gauss's Theorem:** Every positive definite binary quadratic form is equivalent to at least one reduced form, and each proper equivalence class has a reduced representative. For a fixed discriminant $\Delta < 0$, there are only **finitely many** reduced forms, so there are only finitely many proper equivalence classes. This finite number of classes is called the **class number**, $h(\Delta)$.

### Algorithm for Reduction

If we are given a positive definite form $(a, b, c)$, how do we find its equivalent reduced form? We repeatedly apply two operations (corresponding to matrix transformations) until the form is reduced:

1. **Translation:** If $|b| > a$, we can replace $x$ with $x + ky$ for some integer $k$ to shift $b$ into the range $(-a, a]$. Specifically, let $k$ be the integer closest to $-b / (2a)$. The new form $(a', b', c')$ is:

   $$
   a' = a,\quad b' = b + 2ak,\quad c' = ak^2 + bk + c
   $$
   
2. **Inversion:** If $a > c$, we swap $x$ and $y$, and negate one of them to keep the determinant $+1$ (e.g., $(x, y) \to (-y, x)$). The new form $(a', b', c')$ is:

   $$
   a' = c,\quad b' = -b,\quad c' = a
   $$

Because each inversion strictly decreases $a$, this process must terminate in a finite number of steps, yielding a reduced form in the same equivalence class.
