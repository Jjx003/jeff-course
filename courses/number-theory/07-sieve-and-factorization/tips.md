# Tips

- **Trial Division:** Use a `while` loop to divide out a factor completely before moving on to the next candidate. For example, if $n$ is divisible by $2$, keep dividing $n$ by $2$ and adding $2$ to your list until $n$ is no longer divisible by $2$.
- **The Leftover:** After you finish trial division up to $\sqrt{n}$, the remaining value of $n$ might not be $1$. If $n > 1$, it means the remaining part is itself a prime number, and you should add it to your list of factors.
- **Sieve Array:** In Python, a boolean list is efficient: `is_prime = [True] * (limit + 1)`.
- **Sieve Step:** Be careful with your inner loop bounds in the sieve. `range(p * p, limit + 1, p)` is an elegant way to iterate over multiples starting from $p^2$.

### Going deeper
- [Sieve of Eratosthenes on Wikipedia](https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes)
