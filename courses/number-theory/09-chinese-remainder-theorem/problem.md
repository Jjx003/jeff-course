# The Chinese Remainder Theorem

Imagine you have a bag of coins. When you count them by 3s, there are 2 left over. When you count them by 5s, there are 3 left over. When you count them by 7s, there are 2 left over. How many coins are in the bag?

This classical problem from the Chinese mathematician Sun Tzu (3rd to 5th century CE) is an example of a system of simultaneous congruences. 

We can write this mathematically as:
$$
x \equiv 2 \pmod{3}
$$

$$
x \equiv 3 \pmod{5}
$$

$$
x \equiv 2 \pmod{7}
$$

The **Chinese Remainder Theorem (CRT)** guarantees that if the moduli are pairwise coprime (i.e., no two moduli share a common factor greater than 1), there exists a unique solution modulo the product of the moduli.

In this module, we will state the theorem formally and walk through a constructive proof that not only proves the existence of a solution but gives us an algorithm to find it.

---

### Recap

Systems of linear congruences appear frequently in cryptography, computer science, and number theory. The Chinese Remainder Theorem is the fundamental tool for resolving them.

[Next up: Implementing the CRT in Code](/tracks/number-theory/problems/crt-implementation)
