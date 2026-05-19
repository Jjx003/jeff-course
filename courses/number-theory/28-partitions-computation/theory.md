# Implementation Theory

Euler's pentagonal recurrence computes the partition function from earlier values:

$$
p(n)=\sum_{k=1}^{\infty}(-1)^{k-1}\left(p(n-g_k)+p(n-g_{-k})\right),
$$

where

$$
g_k=\frac{k(3k-1)}{2}.
$$

The generalized pentagonal numbers appear in the order

$$
1,2,5,7,12,15,\ldots
$$

and the signs come in pairs:

$$
+,+,-,-,+,+,-,-,\ldots
$$

The base case is $p(0)=1$: there is exactly one way to partition zero, the empty partition. Values with negative indices contribute $0$.
