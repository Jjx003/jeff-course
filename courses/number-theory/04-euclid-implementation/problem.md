# The Euclidean Algorithm

The Greatest Common Divisor (GCD) of two integers $a$ and $b$ is the largest positive integer that divides both $a$ and $b$ without a remainder.

The ancient Greek mathematician Euclid described an elegant and efficient algorithm for computing the GCD over two millennia ago. The algorithm is based on the principle that the greatest common divisor of two numbers does not change if the larger number is replaced by its difference with the smaller number. In its modern form, it uses the remainder of division (the modulo operator `%`).

## The Problem

Your task is to write a function `gcd(a, b)` that takes two non-negative integers and returns their greatest common divisor. You should implement this using the Euclidean algorithm rather than relying on built-in math libraries.

### Constraints
- $0 \le a, b \le 10^{18}$
- At least one of $a$ or $b$ will be non-zero.
- The standard convention is that $\gcd(a, 0) = a$.

### Expected Output

Your program will test your function against several pairs of numbers. You should print the result of `gcd(a, b)` for each pair.
