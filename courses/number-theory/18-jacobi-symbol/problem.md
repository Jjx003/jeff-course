The **Jacobi symbol** $\left(\frac{a}{n}\right)$ is a generalization of the Legendre symbol. It is defined for any integer $a$ and any positive odd integer $n$. 

While it does not tell us directly whether $a$ is a quadratic residue modulo $n$ (unless $n$ is prime), it is incredibly useful because it can be calculated **without factoring $n$**, using properties analogous to the Euclidean algorithm.

### The Problem

Write a function `jacobi_symbol(a, n)` that computes the Jacobi symbol $\left(\frac{a}{n}\right)$ for an integer $a \ge 0$ and an odd integer $n \ge 3$.

You must compute the symbol using the properties of the Jacobi symbol and the **Law of Quadratic Reciprocity**, without attempting to prime factorize $n$.

### Properties of the Jacobi Symbol

For any integers $a, b$ and odd positive integers $m, n$:

1. **Periodicity:** $\left(\frac{a}{n}\right) = \left(\frac{a \pmod n}{n}\right)$
2. **Multiplicativity:** $\left(\frac{ab}{n}\right) = \left(\frac{a}{n}\right)\left(\frac{b}{n}\right)$
3. **Base cases:**
   - $\left(\frac{1}{n}\right) = 1$
   - $\left(\frac{0}{n}\right) = 0$ (if $n > 1$)
   - $\left(\frac{-1}{n}\right) = 1$ if $n \equiv 1 \pmod 4$, and $-1$ if $n \equiv 3 \pmod 4$.
   - $\left(\frac{2}{n}\right) = 1$ if $n \equiv \pm 1 \pmod 8$, and $-1$ if $n \equiv \pm 3 \pmod 8$.
4. **Law of Quadratic Reciprocity:** For coprime odd positive integers $m, n$:

   $$
   \left(\frac{m}{n}\right)\left(\frac{n}{m}\right) = (-1)^{\frac{m-1}{2}\frac{n-1}{2}}
   $$

   This means $\left(\frac{m}{n}\right) = -\left(\frac{n}{m}\right)$ if $m \equiv n \equiv 3 \pmod 4$, and $\left(\frac{m}{n}\right) = \left(\frac{n}{m}\right)$ otherwise.

### Expected Input and Output
The function should handle large integers efficiently. We will test it against a series of $(a, n)$ pairs.

**Output:**
Return an integer: `1`, `-1`, or `0`.
