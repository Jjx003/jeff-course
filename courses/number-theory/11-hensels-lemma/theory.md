# Lifting Roots with Hensel's Lemma

### The Core Idea

Suppose we have a polynomial $f(x)$ with integer coefficients, and we want to find roots modulo $p^k$. 
Imagine we have already found a root $r$ modulo $p$. This means $f(r) \equiv 0 \pmod{p}$.
Can we find a related root $s$ modulo $p^2$ such that $s \equiv r \pmod{p}$?
Since $s \equiv r \pmod{p}$, we can write $s = r + t p$ for some integer $t$.
Hensel's Lemma gives us a way to solve for this $t$.

### The Formal Statement

Let $f(x)$ be a polynomial with integer coefficients, and let $f'(x)$ be its formal derivative.
Let $p$ be a prime, and let $k \ge 1$ be an integer.
Suppose $r$ is an integer such that:

$$
f(r) \equiv 0 \pmod{p^k}
$$

This means $r$ is a root of $f(x)$ modulo $p^k$. Now we want to lift this to a root $s$ modulo $p^{k+1}$. We write $s = r + t p^k$.

If **$f'(r) \not\equiv 0 \pmod{p}$**, then there exists a **unique** integer $t \pmod{p}$ such that:

$$
f(r + t p^k) \equiv 0 \pmod{p^{k+1}}
$$

Furthermore, this $t$ is given by the formula:

$$
t \equiv -\frac{f(r)}{p^k} \cdot [f'(r)]^{-1} \pmod{p}
$$

### The Proof using Taylor Expansion

Why does this work? It comes directly from the Taylor expansion of polynomials. 
For any polynomial $f(x)$ and any numbers $x$ and $h$, we can write the Taylor expansion:

$$
f(x + h) = f(x) + f'(x)h + \frac{f''(x)}{2!}h^2 + \dots
$$

Notice that since $f(x)$ has integer coefficients, the terms like $\frac{f''(x)}{2!}$ are also polynomials with integer coefficients (you can verify this by taking derivatives of $x^n$).

Let's plug in $x = r$ and $h = t p^k$:

$$
f(r + t p^k) = f(r) + f'(r)(t p^k) + \frac{f''(r)}{2!}(t p^k)^2 + \dots
$$

We are analyzing this modulo $p^{k+1}$. Look at the terms starting from the squared term:
$(t p^k)^2 = t^2 p^{2k}$. Since $k \ge 1$, we know $2k \ge k+1$. Therefore, $p^{2k}$ is a multiple of $p^{k+1}$. 
This means all terms involving $h^2, h^3,$ etc., are congruent to $0 \pmod{p^{k+1}}$.

So the expansion radically simplifies:

$$
f(r + t p^k) \equiv f(r) + f'(r) t p^k \pmod{p^{k+1}}
$$

We want $r + t p^k$ to be a root modulo $p^{k+1}$, meaning we want this expression to be $0 \pmod{p^{k+1}}$:

$$
f(r) + f'(r) t p^k \equiv 0 \pmod{p^{k+1}}
$$

Since $r$ is a root modulo $p^k$, we know $f(r)$ is a multiple of $p^k$. Let's write $f(r) = C p^k$ for some integer $C = \frac{f(r)}{p^k}$.

$$
C p^k + f'(r) t p^k \equiv 0 \pmod{p^{k+1}}
$$

Divide the entire congruence by $p^k$ (this changes the modulo to $p^{k+1} / p^k = p$):
$$
C + f'(r) t \equiv 0 \pmod{p}
$$

$$
f'(r) t \equiv -C \pmod{p}
$$

$$
f'(r) t \equiv -\frac{f(r)}{p^k} \pmod{p}
$$

Since we assumed $f'(r) \not\equiv 0 \pmod{p}$, the value $f'(r)$ is coprime to $p$, meaning it has a modular inverse modulo $p$. We can solve for $t$:

$$
t \equiv -\frac{f(r)}{p^k} \cdot [f'(r)]^{-1} \pmod{p}
$$

This proves the existence and uniqueness of $t$, and gives us an explicit formula to calculate it!

### Newton's Method Analogy

If you rearrange the formula for the lifted root $s = r + t p^k$, you get:

$$
s = r - \frac{f(r)}{f'(r)}
$$

This is exactly the formula for Newton-Raphson approximation in calculus! The only difference is we are operating in the world of modular arithmetic (specifically, $p$-adic numbers).

![Hensel's Lift](/courses/number-theory/hensels-lift.svg)
