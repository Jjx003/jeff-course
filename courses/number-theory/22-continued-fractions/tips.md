### Visualizing the Recurrences

When computing convergents by hand, it can be extremely helpful to set up a table. Let's compute the convergents for $x = [2; 1, 4, 3]$ (which is $45/16$).

| $n$ | $-2$ | $-1$ | $0$ | $1$ | $2$ | $3$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| $a_n$| | | 2 | 1 | 4 | 3 |
| $p_n$| 0 | 1 | 2 | 3 | 14 | 45 |
| $q_n$| 1 | 0 | 1 | 1 | 5 | 16 |

To find the next term in the $p_n$ row, you multiply the current $a_n$ by the previous $p_{n-1}$ and add the $p_{n-2}$ from two steps back.
For example, for $n=2$:
$$p_2 = a_2 \cdot p_1 + p_0 = 4 \cdot 3 + 2 = 14$$
$$q_2 = a_2 \cdot q_1 + q_0 = 4 \cdot 1 + 1 = 5$$

### Going Deeper
* Read more about the amazing properties of continued fractions in Hardy and Wright's *An Introduction to the Theory of Numbers*.
* Consider how infinite continued fractions relate to the roots of quadratic equations. We will explore this connection when studying Pell's Equation!
