# The Cheat Sheet

| Distribution | Mean | Variance |
|---|---|---|
| Bernoulli($p$) | $p$ | $p(1-p)$ |
| Binomial($n,p$) | $np$ | $np(1-p)$ |
| Poisson($\lambda$) | $\lambda$ | $\lambda$ |
| Geometric($p$) | $1/p$ | $(1-p)/p^2$ |
| Uniform($a,b$) | $(a+b)/2$ | $(b-a)^2/12$ |
| Exponential($\lambda$) | $1/\lambda$ | $1/\lambda^2$ |
| Normal($\mu,\sigma^2$) | $\mu$ | $\sigma^2$ |

| Result | Value |
|---|---|
| Coupon collector | $nH_n \approx n\ln n$ |
| Expected fixed points of a random permutation | 1 |
| Expected flips until HH | 6 |
| Expected flips until HT | 4 |
| Fair gambler's ruin from $i$ to $N$ | $i/N$ |
| Geometric series $\sum_{k\ge0}r^k$ | $1/(1-r)$ for $\lvert r\rvert<1$ |

# How to Attack a Probability Question

1. **Classify it.** Waiting? Counting? Updating a belief? Use the table in the overview.
2. **Try linearity of expectation first.** It needs no independence and turns most "expected number of X" questions into a sum of indicator probabilities.
3. **If there is a state that evolves, use first-step analysis.** Condition on the first step, write the recurrence, solve.
4. **If it feels like it needs a sum over all cases, look again.** Interview probability questions almost never need one; there is usually a decomposition.
5. **Sanity check the answer.** Is it in $[0,1]$ for a probability? Does it go the right way in the limits? Does it match a simple special case you can compute by hand?

That last step is worth doing out loud. Catching your own error before the interviewer does is a positive signal, not a negative one.

# Rapid-Fire Answers

**"Expected flips until HH versus HT, and why do they differ?"**
> 6 and 4. With HT, a failure (seeing another H) leaves you in a useful state — you are still one T from success. With HH, a failure (seeing a T) sends you back to the start. Overlapping patterns are worse.

**"Why is a positive test only 50% informative?"**
> When the base rate equals the false-positive rate, true positives and false positives are equally numerous. 1% prevalence with 99% specificity gives 0.99% true positives and 0.99% false positives.

**"When is uncorrelated the same as independent?"**
> For jointly Gaussian variables it does. In general it does not — uncorrelated only means zero *linear* dependence. The standard counterexample is $X$ and $X^2$ for $X$ symmetric **about zero**: the symmetry is what kills the covariance, and it fails otherwise ($X \sim N(3,1)$ gives a correlation of 0.97). Note the converse direction is not universal either — for two binary variables, zero covariance does imply independence.

**"What does positive definite mean and why do you care?"**
> For a symmetric matrix: all eigenvalues positive, equivalently $x^\top A x > 0$ for all nonzero $x$. (The equivalence needs the symmetry; in context — Hessians, covariances — you always have it.) A positive-definite Hessian at a critical point means a local minimum. High-dimensional optimization works because saddles vastly outnumber minima and gradient methods escape them.

**"Why does the SVD justify LoRA?"**
> Truncating to the top $k$ singular values gives the best rank-$k$ approximation. If fine-tuning updates have low intrinsic rank, a rank-$r$ factorization captures them, and you train $r(d_{in}+d_{out})$ parameters instead of $d_{in}d_{out}$.

# Further Reading

- [Alisa's math notes](https://alisawuffles.notion.site/math-notes) — built for exactly this interview, and the source of the technique-selection framing used here.
- [Introduction to Probability](https://projects.iq.harvard.edu/stat110/home) — Blitzstein's course. The best treatment of first-step analysis and indicator decomposition anywhere.
- [The Matrix Cookbook](https://www.math.uwaterloo.ca/~hwolkowi/matrixcookbook.pdf) — a reference, not a read.
- [Mathematics for Machine Learning](https://mml-book.github.io/) — free, and the right level for filling gaps.
- [Fifty Challenging Problems in Probability](https://store.doverpublications.com/0486653552.html) — Mosteller. Where a lot of interview puzzles come from.
