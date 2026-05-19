# Tips

- **Base Case:** Don't forget to handle the case where $b = 0$. This is the stopping condition for your loop or recursion.
- **Iteration vs. Recursion:** You can write this algorithm either iteratively (using a `while` loop) or recursively. Both are fine, but an iterative approach avoids the overhead of function calls.
- **Swapping variables:** In Python, you can update two variables simultaneously. The update step `a = b` and `b = a % b` can be written elegantly in one line: `a, b = b, a % b`.

### Going deeper

- [Euclidean algorithm on Wikipedia](https://en.wikipedia.org/wiki/Euclidean_algorithm)
