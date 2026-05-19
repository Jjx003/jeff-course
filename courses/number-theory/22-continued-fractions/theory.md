### 1. Generating Continued Fractions

To find the continued fraction expansion of a real number $x$, we use a simple iterative process:

1. Let $x_0 = x$.
2. The integer part is $a_n = \lfloor x_n \rfloor$.
3. If $x_n - a_n = 0$, we stop. Otherwise, the remainder is fractional, so we set $x_{n+1} = \frac{1}{x_n - a_n}$ and repeat.

For a rational number, this process is exactly the Euclidean algorithm and must terminate, yielding a finite continued fraction $[a_0; a_1, \dots, a_n]$. For an irrational number, it continues indefinitely, yielding $[a_0; a_1, a_2, \dots]$.

![Continued Fractions](/courses/number-theory/continued-fractions.svg)

### 2. Convergents

If we truncate a continued fraction at the $k$-th step, we get a rational number called the $k$-th **convergent**, denoted $C_k = \frac{p_k}{q_k}$:

$$
C_k = [a_0; a_1, \dots, a_k]
$$

We can compute the numerators $p_k$ and denominators $q_k$ using a set of elegant recurrence relations. We define the initial values as:

$$
\begin{aligned}
p_{-2} &= 0, \quad p_{-1} = 1 \\
q_{-2} &= 1, \quad q_{-1} = 0
\end{aligned}
$$

For $k \ge 0$, the recurrence is:

$$
\begin{aligned}
p_k &= a_k p_{k-1} + p_{k-2} \\
q_k &= a_k q_{k-1} + q_{k-2}
\end{aligned}
$$

### 3. Fundamental Identity of Convergents

A crucial property of the convergents is that successive convergents satisfy the identity:

$$
p_n q_{n-1} - p_{n-1} q_n = (-1)^{n-1}
$$

**Proof:** We prove the identity by induction. For $n=0$, the left-hand side is:

$$
p_0 q_{-1} - p_{-1} q_0 = (a_0)(0) - (1)(1) = -1
$$

This is the value prescribed by $(-1)^{n-1}$ when $n=0$. Assume the identity holds for $n=k$:

$$
p_k q_{k-1} - p_{k-1} q_k = (-1)^{k-1}
$$

Now consider $n=k+1$:

$$
\begin{aligned}
p_{k+1} q_k - p_k q_{k+1} &= (a_{k+1} p_k + p_{k-1}) q_k - p_k (a_{k+1} q_k + q_{k-1}) \\
&= a_{k+1} p_k q_k + p_{k-1} q_k - a_{k+1} p_k q_k - p_k q_{k-1} \\
&= p_{k-1} q_k - p_k q_{k-1} \\
&= -(p_k q_{k-1} - p_{k-1} q_k) \\
&= -(-1)^{k-1} = (-1)^k
\end{aligned}
$$
Thus, the identity holds for all $n \ge 0$. $\blacksquare$

Dividing both sides by $q_n q_{n-1}$, we get an expression for the difference between successive convergents:

$$
\frac{p_n}{q_n} - \frac{p_{n-1}}{q_{n-1}} = \frac{(-1)^{n-1}}{q_n q_{n-1}}
$$

For an irrational $x$, this shows that the convergents $C_n$ alternate around the true value:

$$
C_0 < C_2 < C_4 < \dots < x < \dots < C_5 < C_3 < C_1
$$

### 4. Best Rational Approximations

Convergents provide exceptionally good rational approximations to $x$. If $x$ is a real number and $\frac{p_n}{q_n}$ is its $n$-th convergent, we have the inequality:

$$
\left| x - \frac{p_n}{q_n} \right| \le \frac{1}{q_n q_{n+1}} < \frac{1}{q_n^2}
$$

Even more remarkably, properties of continued fractions tell us that convergents are **best approximations of the second kind**: if $\frac{a}{b} \ne \frac{p_n}{q_n}$ is any rational number with $0 < b \le q_n$, then:

$$
|q_n x - p_n| < |b x - a|
$$

This is a slightly stronger denominator-weighted statement than comparing decimal errors alone, and it is the reason continued fractions are so effective at finding rational approximations (for example, $\frac{22}{7}$ and $\frac{355}{113}$ for $\pi$).
