# The Order of an Element

Let $n > 1$ and $\gcd(a, n) = 1$. The **order** of $a$ modulo $n$, denoted as $\text{ord}_n(a)$, is the smallest positive integer $k$ such that:

$$
a^k \equiv 1 \pmod n
$$

### Properties of the Order

The order has some crucial properties:
1. **It divides $\phi(n)$.** By Euler's Totient Theorem, $a^{\phi(n)} \equiv 1 \pmod n$. More generally, if $a^m \equiv 1 \pmod n$, then $\text{ord}_n(a) \mid m$. Thus, the order must be a divisor of $\phi(n)$.
2. **Cyclic behavior.** The powers $a^1, a^2, \dots, a^k$ are all distinct modulo $n$, where $k = \text{ord}_n(a)$. After that, the sequence repeats.

![Order Cycle](/courses/number-theory/order-cycle.svg)

3. **Condition for $a^i \equiv a^j$.** $a^i \equiv a^j \pmod n$ if and only if $i \equiv j \pmod{\text{ord}_n(a)}$.


### Primitive Roots

If $\text{ord}_n(a) = \phi(n)$, we say that $a$ is a **primitive root** modulo $n$.

If a primitive root $g$ exists modulo $n$, then the powers $g^1, g^2, \dots, g^{\phi(n)}$ generate all $\phi(n)$ numbers coprime to $n$. In this case, we say that the multiplicative group of integers modulo $n$, denoted $(\mathbb{Z}/n\mathbb{Z})^\times$, is **cyclic**, and $g$ is a **generator**.

### Does a primitive root always exist?

No! Primitive roots only exist for specific values of $n$.
A primitive root modulo $n$ exists if and only if $n$ is of the form:

$$
2,\ 4,\ p^k,\ \text{or } 2p^k
$$

where $p$ is an odd prime and $k \ge 1$.

For example, $n = 8$ has no primitive roots. The numbers coprime to 8 are 1, 3, 5, 7. Let's check their powers:

- $1^1 = 1$
- $3^2 = 9 \equiv 1 \pmod 8$
- $5^2 = 25 \equiv 1 \pmod 8$
- $7^2 = 49 \equiv 1 \pmod 8$

All elements square to 1, so the maximum order is 2. However, $\phi(8) = 4$. Since no element has order 4, there are no primitive roots modulo 8.

### Proof of Existence Modulo a Prime

Let $p$ be a prime. We want to prove that a primitive root exists modulo $p$. 

First, recall a theorem about polynomials over fields: A polynomial of degree $d$ can have at most $d$ roots modulo $p$.

For any divisor $d$ of $p-1$, the polynomial $x^d - 1 \equiv 0 \pmod p$ has exactly $d$ roots. 
Let $\psi(d)$ be the number of elements modulo $p$ that have order *exactly* $d$.
Every element from $1$ to $p-1$ has some order $d$ that divides $p-1$. Therefore:

$$
\sum_{d \mid (p-1)} \psi(d) = p - 1
$$

However, there's another identity involving divisors:

$$
\sum_{d \mid (p-1)} \phi(d) = p - 1
$$

If an element $a$ has order $d$, then its powers $a, a^2, \dots, a^d=1$ are all solutions to $x^d - 1 \equiv 0 \pmod p$. In fact, these are *all* $d$ solutions. Which of these have order exactly $d$? The elements of the form $a^k$ where $\gcd(k, d) = 1$. There are exactly $\phi(d)$ such elements. 
This means if there is *at least one* element of order $d$, there are exactly $\phi(d)$ of them. So $\psi(d)$ is either 0 or $\phi(d)$.

Since the sums of $\psi(d)$ and $\phi(d)$ both equal $p-1$, we must have $\psi(d) = \phi(d)$ for all divisors $d$.
Specifically, for $d = p-1$, we have $\psi(p-1) = \phi(p-1)$. 
Since $\phi(p-1) > 0$ for $p > 2$, there is always at least one element of order $p-1$. This element is a primitive root!
