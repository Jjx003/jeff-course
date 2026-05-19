# Primitive Roots

Now that we have established Fermat's Little Theorem and Euler's Totient Theorem, we know that for any integer $a$ coprime to $n$, we have:
$$
a^{\phi(n)} \equiv 1 \pmod n
$$

But does it always take $\phi(n)$ powers to reach 1? Sometimes, smaller powers will suffice. The smallest positive integer $k$ such that $a^k \equiv 1 \pmod n$ is called the **order** of $a$ modulo $n$.

In this module, we will explore the properties of the order of an element, and what happens when the order is as large as possible—exactly $\phi(n)$. Such elements are called **primitive roots**.

Read the theory section to understand how primitive roots work, when they exist, and how to prove their properties!
