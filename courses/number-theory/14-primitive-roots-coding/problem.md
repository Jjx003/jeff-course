# Finding a Primitive Root

Given a prime number $p$, your task is to find the **smallest positive primitive root** modulo $p$.

Recall that a number $g$ is a primitive root modulo $p$ if its order is exactly $p-1$. In other words, $g^k \not\equiv 1 \pmod p$ for all $1 \le k < p-1$, and $g^{p-1} \equiv 1 \pmod p$.

Checking every power of $g$ from $1$ to $p-1$ would be too slow. Instead, you can use the property that the order of any element must divide $p-1$. 

Therefore, $g$ is a primitive root modulo $p$ if and only if for every prime factor $q$ of $p-1$:
$$
g^{(p-1)/q} \not\equiv 1 \pmod p
$$

### Input
A single prime number $p$ where $3 \le p \le 10^9$.

### Output
Return the smallest primitive root $g \in \{2, \dots, p-1\}$.

### Example
If $p = 7$, $p-1 = 6$. The prime factors of 6 are 2 and 3.
Let's check $g=2$:
$2^{6/2} = 2^3 = 8 \equiv 1 \pmod 7$. Thus, 2 is not a primitive root.
Let's check $g=3$:
$3^{6/2} = 3^3 = 27 \equiv 6 \not\equiv 1 \pmod 7$
$3^{6/3} = 3^2 = 9 \equiv 2 \not\equiv 1 \pmod 7$
So 3 is the smallest primitive root.
