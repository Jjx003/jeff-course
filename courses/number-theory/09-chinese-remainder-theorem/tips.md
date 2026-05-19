# Tips

- **Pairwise Coprime:** It's crucial that the moduli are *pairwise* coprime. If they aren't, the standard CRT doesn't apply directly (though a generalized version exists, which involves checking consistency conditions and working modulo the LCM of the moduli).
- **Constructive Proof:** The proof provided is not just abstract nonsense; it's a direct recipe. If you need to solve a system by hand, just follow the steps of computing $M$, $M_i$, $y_i$, and the final sum.
- **Finding Inverses:** In step 3, you need to find the modular inverse. For small numbers, trial and error works. For larger numbers, you should use the Extended Euclidean Algorithm, which you implemented in earlier modules.

### Going deeper
- [Chinese Remainder Theorem on Wikipedia](https://en.wikipedia.org/wiki/Chinese_remainder_theorem)
