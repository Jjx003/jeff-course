# Tips for Quadratic Reciprocity

- **Don't Forget to Factor:** The Law of Quadratic Reciprocity only applies to *distinct odd primes*. If you are evaluating $\left(\frac{a}{p}\right)$, you must first factor $a$ into primes.
- **The $3 \pmod 4$ Rule:** When flipping $\left(\frac{p}{q}\right)$ to $\left(\frac{q}{p}\right)$, the sign changes *only* if both $p$ and $q$ leave a remainder of $3$ when divided by $4$. Otherwise, the sign stays the same.
- **Modulo Reduction:** After flipping, always reduce the "numerator" (the top number) modulo the "denominator" (the bottom number) to make the numbers smaller.
- **The Jacobi Symbol:** In practice, having to factor $a$ can be slow if $a$ is very large. A generalization called the **Jacobi Symbol** allows us to apply the Law of Quadratic Reciprocity even if the bottom number is not prime, completely bypassing the need to factor! We will explore this in the next module.

### Going Deeper

- [Quadratic reciprocity (Wikipedia)](https://en.wikipedia.org/wiki/Quadratic_reciprocity)
- [Gauss's lemma (number theory) (Wikipedia)](https://en.wikipedia.org/wiki/Gauss%27s_lemma_(number_theory))
