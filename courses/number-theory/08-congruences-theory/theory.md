# Congruences and Modular Arithmetic

## The Definition of Congruence

Let $m$ be a positive integer, which we call the **modulus**. Two integers $a$ and $b$ are said to be **congruent modulo $m$** if $m$ divides their difference $a - b$.

We write this mathematically as:

$$a \equiv b \pmod{m}$$

By definition, this is entirely equivalent to saying that there exists some integer $k$ such that:

$$a - b = km \quad \text{or} \quad a = b + km$$

Another useful way to think about this is through the division algorithm: $a$ and $b$ are congruent modulo $m$ if and only if they leave the same remainder when divided by $m$.

## Properties of Congruences

Congruence behaves in many ways like standard equality. It is an **equivalence relation**, meaning it is:

1. **Reflexive:** $a \equiv a \pmod{m}$
2. **Symmetric:** If $a \equiv b \pmod{m}$, then $b \equiv a \pmod{m}$
3. **Transitive:** If $a \equiv b \pmod{m}$ and $b \equiv c \pmod{m}$, then $a \equiv c \pmod{m}$

**Proof of Transitivity:**
If $a \equiv b \pmod{m}$, then $m \mid (a - b)$.
If $b \equiv c \pmod{m}$, then $m \mid (b - c)$.
Therefore, $m$ divides their sum: $(a - b) + (b - c) = a - c$.
Thus, $a \equiv c \pmod{m}$. $\blacksquare$

### Modular Arithmetic Operations

If $a \equiv b \pmod{m}$ and $c \equiv d \pmod{m}$, then we can perform arithmetic:

**Addition:**
$$a + c \equiv b + d \pmod{m}$$

**Subtraction:**
$$a - c \equiv b - d \pmod{m}$$

**Multiplication:**
$$ac \equiv bd \pmod{m}$$

**Proof for Multiplication:**
Since $a \equiv b \pmod{m}$, we can write $a = b + km$ for some integer $k$.
Since $c \equiv d \pmod{m}$, we can write $c = d + jm$ for some integer $j$.
Multiplying them together:
$$ac = (b + km)(d + jm) = bd + bjm + dkm + kj m^2 = bd + m(bj + dk + kjm)$$
This means $ac - bd$ is a multiple of $m$, so $ac \equiv bd \pmod{m}$. $\blacksquare$

### Exponentiation

A direct consequence of the multiplication rule is that we can raise congruences to integer powers.
If $a \equiv b \pmod{m}$, then for any positive integer $k$:

$$a^k \equiv b^k \pmod{m}$$

This property is incredibly powerful for computing large powers modulo $m$.

## Division in Modular Arithmetic

While addition, subtraction, and multiplication carry over perfectly from standard arithmetic, **division is dangerous**. 

We cannot simply cancel a common factor from a congruence. For example:

$$2 \cdot 4 \equiv 2 \cdot 1 \pmod{6}$$
$$8 \equiv 2 \pmod{6}$$

This is a true statement. However, if we "divide" both sides by $2$, we get:

$$4 \equiv 1 \pmod{6}$$

This is **false**! The reason division failed here is that the factor we divided by ($2$) shares a common divisor with the modulus ($6$). 

**The Cancellation Law:**
You can divide both sides of a congruence $ac \equiv bc \pmod{m}$ by $c$ **only if** $\gcd(c, m) = 1$. 

**Theorem:**
If $ac \equiv bc \pmod{m}$ and $\gcd(c, m) = d$, then:

$$a \equiv b \pmod{\frac{m}{d}}$$

**Proof:**
We know $m \mid (ac - bc)$, which means $m \mid c(a - b)$.
We can write $m = dm'$ and $c = dc'$, where $\gcd(c', m') = 1$.
Substituting these gives $dm' \mid dc'(a - b)$, which simplifies to $m' \mid c'(a - b)$.
Since $\gcd(c', m') = 1$, by Euclid's Lemma, $m'$ must divide $a - b$.
Thus, $a \equiv b \pmod{m'}$, which is exactly $a \equiv b \pmod{\frac{m}{d}}$. $\blacksquare$

If $\gcd(c, m) = 1$, then $d=1$, and we safely get $a \equiv b \pmod{m}$.

## Modular Inverses

Instead of "dividing," we typically multiply by a **modular inverse**.
An integer $x$ is the modular inverse of $a$ modulo $m$ if:

$$ax \equiv 1 \pmod{m}$$

This inverse exists **if and only if** $\gcd(a, m) = 1$. You will explore algorithms to compute modular inverses and solve linear congruences in the next topics.