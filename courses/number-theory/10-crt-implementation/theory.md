# Implementation Theory

The constructive Chinese Remainder Theorem gives a direct algorithm for pairwise coprime moduli $m_1,\ldots,m_k$.

Let

$$
M=m_1m_2\cdots m_k,\qquad M_i=\frac{M}{m_i}.
$$

Since the moduli are pairwise coprime, $\gcd(M_i,m_i)=1$, so $M_i$ has a modular inverse modulo $m_i$. Call that inverse $y_i$:

$$
M_i y_i \equiv 1 \pmod {m_i}.
$$

Now form

$$
x=\sum_i a_i M_i y_i.
$$

Modulo $m_i$, the $i$th term contributes $a_i$, while every other term contains a factor of $m_i$ and contributes $0$. Therefore $x \equiv a_i \pmod {m_i}$ for every $i$.

Python's `pow(Mi, -1, m)` computes the modular inverse directly.
