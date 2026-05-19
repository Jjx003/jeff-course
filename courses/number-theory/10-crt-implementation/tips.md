# Tips

- **Modular Inverse:** You'll need a helper function to compute the modular inverse. You can implement the Extended Euclidean Algorithm for this.
- **Python's built-in:** Python 3.8+ has a built-in `pow(base, -1, mod)` which computes the modular inverse! If you want to use it, you can. If you want to write your own `extGCD` for practice, even better.
- **The Construction:** Remember the formula: $x = \sum (a_i \cdot M_i \cdot y_i) \pmod M$, where $M_i = M / m_i$ and $y_i$ is the inverse of $M_i \pmod{m_i}$.
- **Modulo M at the end:** Don't forget to take the final sum modulo $M$ (the product of all moduli) to ensure you return the *smallest* non-negative solution.
