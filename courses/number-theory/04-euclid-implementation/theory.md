# Divisibility and the GCD

At the heart of number theory is the concept of **divisibility**. We say that an integer $a$ divides an integer $b$ (written $a \mid b$) if there exists some integer $k$ such that $b = a \cdot k$.

The **Greatest Common Divisor (GCD)** of two numbers is exactly what its name suggests. For instance, the divisors of 12 are $1, 2, 3, 4, 6, 12$ and the divisors of 18 are $1, 2, 3, 6, 9, 18$. The largest number present in both lists is $6$, so $\gcd(12, 18) = 6$.

## Euclid's Observation

Calculating divisors by listing all of them is slow. Euclid observed a structural property of divisibility:

If $d$ divides both $a$ and $b$ (assume $a > b$), then $d$ must also divide their difference, $a - b$. 

Because any divisor of $a$ and $b$ is also a divisor of $a - b$, the problem of finding $\gcd(a, b)$ is identical to finding $\gcd(a - b, b)$. We can repeatedly subtract $b$ from $a$ until $a$ becomes smaller than $b$.

Repeated subtraction is exactly what division gives us! When we divide $a$ by $b$, we get a quotient $q$ and a remainder $r$:
$$
a = b \cdot q + r
$$

Which means $r = a - b \cdot q$. By the same logic as the subtraction observation, any common divisor of $a$ and $b$ must also divide the remainder $r$. 

This leads to the fundamental recurrence of the Euclidean Algorithm:
$$
\gcd(a, b) = \gcd(b, a \bmod b)
$$

## The Algorithm

The process is remarkably simple:
1. If $b = 0$, the GCD is simply $a$.
2. Otherwise, recursively (or iteratively) compute $\gcd(b, a \bmod b)$.

### Example: $\gcd(1071, 462)$

1. $1071 \pmod{462} = 147$
2. The problem reduces to $\gcd(462, 147)$
3. $462 \pmod{147} = 21$
4. The problem reduces to $\gcd(147, 21)$
5. $147 \pmod{21} = 0$
6. The problem reduces to $\gcd(21, 0)$

Since the second argument is now 0, we return the first argument: **21**.
