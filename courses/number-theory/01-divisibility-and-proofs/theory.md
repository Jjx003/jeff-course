# The Formal Definition of Divisibility

In everyday language, we say that "$2$ divides $6$" because $6 \div 2 = 3$ without any remainder. In rigorous number theory, we avoid fractions and division operations, defining divisibility purely in terms of multiplication of integers.

**Definition:** Let $a$ and $b$ be integers with $a \neq 0$. We say that **$a$ divides $b$**, denoted as $a \mid b$, if there exists an integer $k$ such that:

$$
b = a \cdot k
$$

If no such integer $k$ exists, we write $a \nmid b$.

For example:
- $3 \mid 12$ because $12 = 3 \cdot 4$.
- $-5 \mid 30$ because $30 = (-5) \cdot (-6)$.
- $7 \nmid 16$ because there is no integer $k$ for which $16 = 7k$.

### Fundamental Properties of Divisibility

From this single definition, we can rigorously prove several foundational theorems.

**Theorem 1 (Transitivity):** For any integers $a, b, c$ with $a \neq 0$ and $b \neq 0$, if $a \mid b$ and $b \mid c$, then $a \mid c$.

**Proof:**
By the definition of divisibility, since $a \mid b$, there exists an integer $k_1$ such that:
$$
b = a \cdot k_1
$$

Similarly, since $b \mid c$, there exists an integer $k_2$ such that:
$$
c = b \cdot k_2
$$

Substitute the expression for $b$ into the equation for $c$:
$$
c = (a \cdot k_1) \cdot k_2
$$

$$
c = a \cdot (k_1 \cdot k_2)
$$

Let $k_3 = k_1 \cdot k_2$. Since the product of two integers is an integer, $k_3$ is an integer. Thus:
$$
c = a \cdot k_3
$$

By definition, this means $a \mid c$. $\blacksquare$

**Theorem 2 (Linear Combinations):** For any integers $a, b, c, x, y$ with $a \neq 0$, if $a \mid b$ and $a \mid c$, then $a \mid (bx + cy)$.

**Proof:**
Since $a \mid b$, there is an integer $k_1$ such that $b = a \cdot k_1$.
Since $a \mid c$, there is an integer $k_2$ such that $c = a \cdot k_2$.

Consider the expression $bx + cy$:
$$
bx + cy = (a \cdot k_1)x + (a \cdot k_2)y
$$

$$
bx + cy = a(k_1 x + k_2 y)
$$

Let $k_3 = k_1 x + k_2 y$. Since the integers are closed under addition and multiplication, $k_3$ is an integer. Thus, we have expressed $bx + cy$ as $a \cdot k_3$, which means:
$$
a \mid (bx + cy)
$$
$\blacksquare$

## The Division Algorithm

Despite its name, the Division Algorithm is not an algorithm (a sequence of steps) but a fundamental existence and uniqueness theorem regarding integer division.

**Theorem (The Division Algorithm):** Let $a$ and $b$ be integers with $a > 0$. Then there exist unique integers $q$ (the quotient) and $r$ (the remainder) such that:

$$
b = a \cdot q + r \quad \text{where} \quad 0 \leq r < a
$$

This theorem confirms our intuition from elementary school long division: when we divide $b$ by $a$, we get a quotient and a non-negative remainder that is strictly less than the divisor.

**Example:** Let $b = 42$ and $a = 8$.
We find $42 = 8 \cdot 5 + 2$. Here, $q = 5$ and $r = 2$. Notice that $0 \leq 2 < 8$, so the conditions are satisfied.

The Division Algorithm is the cornerstone of number theory. It provides the basis for base representations (like binary or hexadecimal), modular arithmetic, and the Euclidean Algorithm, which we will explore in upcoming modules.
