# Tips for Euler's Criterion

- **Symmetry of Squares:** When listing squares modulo $p$, you only need to compute up to $\frac{p-1}{2}$. The remaining squares will be symmetric because $x^2 \equiv (p-x)^2 \pmod p$.
- **Modular Exponentiation:** Remember that computing $a^{\frac{p-1}{2}} \pmod p$ is fast! You can use the method of successive squaring. This means Euler's Criterion is computationally efficient, taking $O(\log p)$ steps.
- **Wilson's Theorem Reminder:** The proof of Euler's Criterion relies heavily on Wilson's Theorem, which states that for any prime $p$, $(p-1)! \equiv -1 \pmod p$. If you haven't reviewed Wilson's Theorem recently, it's worth a look.

### Going Deeper

- [Legendre symbol (Wikipedia)](https://en.wikipedia.org/wiki/Legendre_symbol)
- [Euler's criterion (Wikipedia)](https://en.wikipedia.org/wiki/Euler%27s_criterion)
