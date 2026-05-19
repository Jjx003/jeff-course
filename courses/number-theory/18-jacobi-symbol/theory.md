The Legendre symbol $\left(\frac{a}{p}\right)$ is defined only when the "denominator" $p$ is prime. To compute it efficiently, we often want to use Quadratic Reciprocity to flip the symbol: $\left(\frac{a}{p}\right) \to \pm \left(\frac{p}{a}\right)$. 

However, if we do this, the new denominator $a$ might not be prime! This means we would have to factor $a$, compute the Legendre symbol for each prime factor, and multiply them together. Factoring is computationally expensive ($O(\exp(c (\log n)^{1/3} (\log \log n)^{2/3}))$).

### Enter the Jacobi Symbol

Carl Gustav Jacob Jacobi generalized the Legendre symbol to any positive odd integer denominator $n$. If $n = p_1^{e_1} p_2^{e_2} \dots p_k^{e_k}$, the Jacobi symbol is defined as:

$$ \left(\frac{a}{n}\right) = \left(\frac{a}{p_1}\right)^{e_1} \dots \left(\frac{a}{p_k}\right)^{e_k} $$

Here, the symbols on the right are Legendre symbols. 

### Why is this useful?

The brilliance of the Jacobi symbol is that **it satisfies the Law of Quadratic Reciprocity** just like the Legendre symbol:

$$ \left(\frac{m}{n}\right) = (-1)^{\frac{m-1}{2}\frac{n-1}{2}} \left(\frac{n}{m}\right) $$

where $m$ and $n$ are both positive, odd, and coprime integers. 

Because of this, we can flip the symbol **without factoring either number**! This leads to a fast, recursive algorithm similar to the Euclidean algorithm for computing the greatest common divisor.

### The Algorithm

To compute $\left(\frac{a}{n}\right)$ where $n$ is an odd positive integer:
1. Reduce $a$ modulo $n$.
2. If $a = 0$, return $0$ (unless $n = 1$, then return $1$).
3. Extract all factors of $2$ from $a$: write $a = 2^k \cdot a'$ where $a'$ is odd.
4. Evaluate $\left(\frac{2^k}{n}\right) = \left(\frac{2}{n}\right)^k$ using the property:
   - $\left(\frac{2}{n}\right) = 1$ if $n \equiv 1$ or $7 \pmod 8$
   - $\left(\frac{2}{n}\right) = -1$ if $n \equiv 3$ or $5 \pmod 8$
5. Apply Quadratic Reciprocity to flip $\left(\frac{a'}{n}\right)$ to $\left(\frac{n}{a'}\right)$, flipping the sign of our running product if $a' \equiv 3 \pmod 4$ and $n \equiv 3 \pmod 4$.
6. Repeat the process with the new symbol $\left(\frac{n \pmod{a'}}{a'}\right)$.

This algorithm runs in $O(\log a \log n)$ bit operations, which is incredibly fast!
