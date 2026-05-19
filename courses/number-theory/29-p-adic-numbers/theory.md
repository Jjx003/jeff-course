## The $p$-adic Valuation and Norm

Let $p$ be a fixed prime number. Any non-zero rational number $x \in \mathbb{Q}$ can be written uniquely as:

$$
x = p^v \frac{a}{b}
$$

where $v \in \mathbb{Z}$, and $a, b$ are integers not divisible by $p$. We define the **$p$-adic valuation** of $x$ as $v_p(x) = v$. By convention, $v_p(0) = \infty$.

The **$p$-adic norm** (or absolute value) of $x$ is then defined as:

$$
|x|_p =
\begin{cases}
p^{-v_p(x)} & \text{if } x \neq 0, \\
0 & \text{if } x = 0.
\end{cases}
$$

### Intuition: "Large" powers of $p$ are "small"
In the $p$-adic world, a number is small if it is divisible by a high power of $p$. 
For example, in $\mathbb{Q}_5$:
- $|25|_5 = 5^{-2} = 1/25$
- $|125|_5 = 5^{-3} = 1/125$
Thus $125$ is "closer" to $0$ than $25$ is.

## The Ultrametric Inequality

The $p$-adic norm satisfies a much stronger version of the triangle inequality, known as the **ultrametric inequality**:

$$
|x + y|_p \le \max(|x|_p, |y|_p)
$$

**Proof:**
Let $x = p^{v_x} \frac{a}{b}$ and $y = p^{v_y} \frac{c}{d}$. Assume without loss of generality that $v_x \le v_y$ (so $|x|_p \ge |y|_p$).
Then

$$
x + y
= p^{v_x} \left( \frac{a}{b} + p^{v_y - v_x} \frac{c}{d} \right)
= p^{v_x} \frac{ad + p^{v_y - v_x}bc}{bd}.
$$

The valuation of the numerator is at least $0$ (since $v_y - v_x \ge 0$). The valuation of the denominator $bd$ is $0$.
Thus $v_p(x+y) \ge v_x = \min(v_p(x), v_p(y))$.
Taking the exponent gives

$$
|x+y|_p = p^{-v_p(x+y)}
\le p^{-\min(v_p(x), v_p(y))}
= \max(|x|_p, |y|_p).
$$

This proves the ultrametric inequality.

This inequality implies that in $\mathbb{Q}_p$, **every triangle is isosceles**, and every point inside a ball is its center!

## Completion: From $\mathbb{Q}$ to $\mathbb{Q}_p$

Just as $\mathbb{R}$ is the set of equivalence classes of Cauchy sequences in $\mathbb{Q}$ under the standard norm, $\mathbb{Q}_p$ is the completion of $\mathbb{Q}$ under the $p$-adic norm $| \cdot |_p$.

A sequence $\{x_n\}$ is **$p$-adically Cauchy** if for every $\epsilon > 0$, there exists $N$ such that $|x_n - x_m|_p < \epsilon$ for all $n, m > N$.

An amazing consequence of the ultrametric inequality is that a series $\sum a_n$ converges in $\mathbb{Q}_p$ **if and only if** $a_n \to 0$.

## $p$-adic Integers $\mathbb{Z}_p$

The set of **$p$-adic integers** $\mathbb{Z}_p$ is the "unit ball" in $\mathbb{Q}_p$:

$$
\mathbb{Z}_p = \{ x \in \mathbb{Q}_p : |x|_p \le 1 \}
$$

Every $x \in \mathbb{Z}_p$ has a unique representation as an infinite power series in $p$:

$$
x = a_0 + a_1 p + a_2 p^2 + a_3 p^3 + \dots
$$

where $a_i \in \{0, 1, \dots, p-1\}$. This looks like a base-$p$ expansion that goes "to the left" infinitely. We can visualize $\mathbb{Z}_p$ as an infinite tree, where each level represents the expansion modulo $p^k$:

![p-adic Tree](/courses/number-theory/p-adic-tree.svg)

## Hensel's Lemma Revisited

We previously saw Hensel's Lemma as a way to lift solutions of $f(x) \equiv 0 \pmod p$ to $p^k$. In $\mathbb{Q}_p$, this is exactly **Newton's Method**.

**Theorem (Hensel's Lemma):** Let $f(x) \in \mathbb{Z}_p[x]$. If there exists $\alpha_0 \in \mathbb{Z}_p$ such that

$$
|f(\alpha_0)|_p < |f'(\alpha_0)|_p^2,
$$

Then there exists a unique $\alpha \in \mathbb{Z}_p$ such that $f(\alpha) = 0$ and $|\alpha - \alpha_0|_p < |f'(\alpha_0)|_p$.

This provides a powerful link between algebra and analysis: we can "solve" equations by starting with an approximate solution and refining it.
