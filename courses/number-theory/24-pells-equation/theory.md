## The Continued Fraction Connection

Suppose $x$ and $y$ are large positive integers satisfying $x^2 - Dy^2 = 1$. We can rewrite this as:

$$ (x - y\sqrt{D})(x + y\sqrt{D}) = 1 $$

Dividing by $y(x + y\sqrt{D})$, we get:

$$ \frac{x}{y} - \sqrt{D} = \frac{1}{y(x + y\sqrt{D})} $$

Because $x$ and $y$ are positive and $x > y\sqrt{D}$, the right-hand side is positive and very small. Specifically, $x / y \approx \sqrt{D}$, so $x + y\sqrt{D} \approx 2y\sqrt{D}$. Thus:

$$ 0 < \frac{x}{y} - \sqrt{D} < \frac{1}{2y^2\sqrt{D}} < \frac{1}{2y^2} $$

A classical theorem by Legendre states that if a rational number $p/q$ satisfies $\left| p/q - \alpha \right| < 1 / (2q^2)$, then $p/q$ **must be a convergent** of the continued fraction of $\alpha$. 

Therefore, any positive solution $(x,y)$ to Pell's equation must come from the convergents of the continued fraction expansion of $\sqrt{D}$.

## The Period of $\sqrt{D}$

The continued fraction of $\sqrt{D}$ is periodic and has a very specific form:

$$ \sqrt{D} = [a_0; \overline{a_1, a_2, \dots, a_{m-1}, 2a_0}] $$

The period begins immediately after the first term $a_0 = \lfloor\sqrt{D}\rfloor$, and the last term of the period is always exactly $2a_0$. Furthermore, the sequence of terms in the period (excluding the last one) is a palindrome: $a_1 = a_{m-1}, a_2 = a_{m-2}$, etc.

Let $h_k / k_k$ be the $k$-th convergent of $\sqrt{D}$. It turns out that:

$$ h_k^2 - D k_k^2 = (-1)^{k-1} Q_{k+1} $$

where $Q_{k+1}$ is an integer that appears in the exact evaluation of the continued fraction. Because the fraction is periodic with period length $m$, the value $Q_{k+1} = 1$ whenever $k+1$ is a multiple of the period length $m$. 

### Finding the Fundamental Solution

The **fundamental solution** $(x_1, y_1)$ is the smallest positive integer solution to $x^2 - Dy^2 = 1$. Based on the period length $m$, we can find it exactly:

1. **If $m$ is even**: The equation $h_k^2 - Dk_k^2 = 1$ is satisfied at the end of the first period. The fundamental solution is:
   $$ (x_1, y_1) = (h_{m-1}, k_{m-1}) $$

2. **If $m$ is odd**: At the end of the first period ($k=m-1$), we get $h_{m-1}^2 - Dk_{m-1}^2 = -1$ (this is sometimes called the negative Pell equation). To get $+1$, we must go to the end of the *second* period:
   $$ (x_1, y_1) = (h_{2m-1}, k_{2m-1}) $$

## Generating All Solutions

Once we have the fundamental solution $(x_1, y_1)$, we can generate all other positive solutions $(x_n, y_n)$ using the algebraic identity:

$$ x_n + y_n\sqrt{D} = (x_1 + y_1\sqrt{D})^n $$

By expanding the right side and matching the rational and irrational parts, we can find $(x_n, y_n)$ for any $n \ge 1$. For example, squaring the fundamental solution gives the second solution:

$$ (x_1 + y_1\sqrt{D})^2 = (x_1^2 + D y_1^2) + (2x_1 y_1)\sqrt{D} $$

So $x_2 = x_1^2 + D y_1^2$ and $y_2 = 2x_1 y_1$.

This multiplicative structure means the solutions grow exponentially, which is why historical mathematicians like Fermat challenged others to solve for $D=61$. The fundamental solution is $x = 1766319049, y = 226153980$, which is remarkably large for such a small $D$!