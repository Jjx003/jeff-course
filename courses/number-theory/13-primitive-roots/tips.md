# Tips and Applications

Primitive roots are foundational in cryptography. Because powers of a primitive root cycle through all possible values coprime to $p$, finding the exponent given the result is hard.

### The Discrete Logarithm Problem

If $g$ is a primitive root modulo $p$, then for any $x \in \{1, \dots, p-1\}$, there exists a unique $k$ such that:
$$ g^k \equiv x \pmod p $$
This $k$ is called the **discrete logarithm** of $x$ with base $g$.
Computing $g^k \pmod p$ is easy (using fast exponentiation), but finding $k$ given $g$ and $x$ is computationally difficult. This asymmetry is the basis for the Diffie-Hellman key exchange and ElGamal encryption.