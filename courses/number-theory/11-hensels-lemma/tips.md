# Tips

- **Singular Roots:** Hensel's Lemma is simple when $f'(r) \not\equiv 0 \pmod p$. If $f'(r) \equiv 0 \pmod p$, the root is called "singular". In this case, you might have no solutions, or you might have $p$ solutions. The analysis becomes more complex.
- **Formal Derivative:** The derivative $f'(x)$ is just computed formally using the power rule (e.g., $(ax^n)' = anx^{n-1}$). No limits required!
- **Step-by-step lifting:** Often, problems will ask you to find a root modulo something like $125 = 5^3$. You would first find a root mod $5$, then lift to mod $25$, then lift to mod $125$. The value $p$ is always 5. 

### Going deeper
- [Hensel's Lemma on Wikipedia](https://en.wikipedia.org/wiki/Hensel%27s_lemma)
- [p-adic Numbers](https://en.wikipedia.org/wiki/P-adic_number)
