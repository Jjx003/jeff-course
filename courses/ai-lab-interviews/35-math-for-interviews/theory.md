# Probability

## The discrete distributions

**Bernoulli($p$)** — one trial.

$$\mathbb{E}[X] = p, \qquad \mathrm{Var}[X] = p(1-p)$$

The derivation uses a trick worth internalizing: for a binary $X \in \{0,1\}$, $X^2 = X$, so $\mathbb{E}[X^2] = \mathbb{E}[X] = p$, and $\mathrm{Var} = p - p^2$.

**Binomial($n,p$)** — the sum of $n$ independent Bernoullis.

$$P(X=k) = \binom{n}{k}p^k(1-p)^{n-k}, \qquad \mathbb{E}[X]=np, \qquad \mathrm{Var}[X]=np(1-p)$$

Never derive these from the PMF. Decompose into indicators and use linearity of expectation for the mean, and independence for the variance. That takes two lines instead of a page.

**Poisson($\lambda$)** — events in a fixed window at rate $\lambda$.

$$P(X=k) = \frac{\lambda^k e^{-\lambda}}{k!}, \qquad \mathbb{E}[X] = \mathrm{Var}[X] = \lambda$$

The derivation to know: it is the binomial limit. Divide the window into $n$ tiny slices, each with at most one event, so the count is Binomial($n$, $p$) with $np = \lambda$; take $n\to\infty$.

Mean equals variance is the fingerprint. Count data whose variance exceeds its mean is *overdispersed* and is not Poisson — a good thing to notice out loud.

**Geometric($p$)** — trials until the first success, inclusive.

$$P(X=k) = (1-p)^{k-1}p, \qquad \mathbb{E}[X] = \frac{1}{p}, \qquad \mathrm{Var}[X] = \frac{1-p}{p^2}$$

**Memorylessness:** $P(X > m+n \mid X > m) = P(X > n)$. Having failed $m$ times tells you nothing. The geometric is the *only* memoryless distribution on the positive integers, and the exponential is the only one on the positive reals — so "memoryless" in a question is a direct pointer to one of those two.

## The continuous distributions

**Uniform($a,b$):** $\mathbb{E} = \frac{a+b}{2}$, $\mathrm{Var} = \frac{(b-a)^2}{12}$.

**Exponential($\lambda$):** $f(x) = \lambda e^{-\lambda x}$, $\mathbb{E} = 1/\lambda$, $\mathrm{Var} = 1/\lambda^2$. Memoryless, and the waiting time between Poisson events.

**Gaussian($\mu,\sigma^2$):** the CLT limit. Worth knowing: a sum of independent Gaussians is Gaussian with means and variances adding; any affine transform of a Gaussian is Gaussian; and for a multivariate Gaussian, uncorrelated implies independent (which is *not* true in general).

## The techniques

### Linearity of expectation

$$\mathbb{E}\left[\sum_i X_i\right] = \sum_i \mathbb{E}[X_i]$$

**Independence is not required.** This is the most powerful and most underused tool in interview probability, because it lets you decompose a horrible dependent problem into trivial indicator variables.

*Coupon collector.* How many draws to collect all $n$ coupons? Let $T_i$ be the additional draws needed to go from $i-1$ to $i$ distinct coupons. $T_i$ is geometric with success probability $(n-i+1)/n$, so $\mathbb{E}[T_i] = n/(n-i+1)$, and

$$\mathbb{E}[T] = \sum_{i=1}^{n}\frac{n}{n-i+1} = n H_n \approx n\ln n$$

*Expected fixed points of a random permutation.* Let $X_i$ indicate that element $i$ maps to itself. $\mathbb{E}[X_i] = 1/n$, so the expected number is $n \cdot 1/n = 1$ — regardless of $n$. The $X_i$ are dependent, and it does not matter.

### First-step analysis

For anything with the Markov property, condition on the first step and solve the resulting recurrence.

*Gambler's ruin.* You have $i$ pounds, win one with probability $p$ and lose one with probability $q=1-p$, and stop at $0$ or $N$. With $P_i$ the probability of reaching $N$:

$$P_i = pP_{i+1} + qP_{i-1}, \qquad P_0 = 0,\ P_N = 1$$

For the fair case $p=q=1/2$ the solution is linear: $P_i = i/N$.

*Expected coin flips until HH.* Let $E$ be the expected flips from the start, $E_H$ the expected additional flips having just seen one head.

$$E = \tfrac12(1+E_H) + \tfrac12(1+E), \qquad E_H = \tfrac12(1) + \tfrac12(1+E)$$

Solving gives $E = 6$. For HT the answer is 4 — and being able to explain *why the two differ* (failing HT leaves you in a useful state; failing HH sends you back to the start) is the follow-up that actually gets scored.

### Bayes' rule and base rates

$$P(A\mid B) = \frac{P(B\mid A)P(A)}{P(B)}$$

The classic setup: a disease with 1% prevalence, a test with 99% sensitivity and 99% specificity. A positive result means

$$P(D\mid +) = \frac{0.99\times0.01}{0.99\times0.01 + 0.01\times0.99} = 0.5$$

Fifty percent, not 99%. The lesson to state: when the base rate is comparable to the false-positive rate, a positive result is roughly a coin flip. Most people's intuition is badly wrong here, which is exactly why it is asked.

### Jensen's inequality

For convex $f$: $\mathbb{E}[f(X)] \ge f(\mathbb{E}[X])$, reversed for concave $f$.

Consequences that come up constantly: $\mathbb{E}[X^2] \ge \mathbb{E}[X]^2$ (which *is* the statement that variance is non-negative), and $\mathbb{E}[\log X] \le \log\mathbb{E}[X]$ — the inequality behind the ELBO in variational inference.

### Concentration

**Markov:** $P(X \ge a) \le \mathbb{E}[X]/a$ for non-negative $X$. Needs only the mean.

**Chebyshev:** $P(|X-\mu| \ge k\sigma) \le 1/k^2$. Needs mean and variance.

**Chernoff / Hoeffding:** exponentially tighter, for bounded independent variables. If a question gives you only a mean, it wants Markov; mean and variance, Chebyshev.

# Linear Algebra

## Eigenvalues

$Av = \lambda v$. For a **symmetric** matrix, eigenvalues are real and eigenvectors are orthogonal — which is why covariance matrices and Hessians are so tractable.

$$\mathrm{tr}(A) = \sum_i\lambda_i, \qquad \det(A) = \prod_i\lambda_i$$

Both are worth knowing as fast sanity checks.

**Positive definite** — for a symmetric matrix — means all eigenvalues are positive, equivalently $x^{\top}Ax > 0$ for all $x \ne 0$. (The equivalence needs the symmetry, which Hessians and covariance matrices always have.) A Hessian that is positive definite at a critical point means a local minimum; indefinite means a saddle. The reason high-dimensional non-convex optimization works at all is that saddles vastly outnumber local minima, and gradient methods escape saddles.

## SVD

$$A = U\Sigma V^{\top}$$

for any matrix. Singular values are the square roots of the eigenvalues of $A^{\top}A$. The rank is the number of non-zero singular values, and truncating to the top $k$ gives the best rank-$k$ approximation in Frobenius norm — the Eckart-Young theorem.

**Why an interviewer cares:** this is the theoretical justification for LoRA. If weight *updates* during fine-tuning have low intrinsic rank, then a rank-$r$ factorization $BA$ captures them, and you train $r(d_{in}+d_{out})$ parameters instead of $d_{in}d_{out}$.

## Norms

$\|x\|_1$ (sum of absolute values), $\|x\|_2$ (Euclidean), $\|x\|_\infty$ (max). The Frobenius norm of a matrix is the $\ell_2$ norm of its flattened entries.

$\ell_1$ regularization induces sparsity because its constraint region has corners on the axes, and the optimum of a smooth objective over that region tends to land on one. $\ell_2$ shrinks without zeroing.

# Calculus

## Derivatives to produce cold

$$\frac{d}{dx}\sigma(x) = \sigma(x)(1-\sigma(x))$$

$$\frac{d}{dx}\tanh(x) = 1-\tanh^2(x)$$

$$\frac{\partial}{\partial z}\big[-\log\mathrm{softmax}(z)_t\big] = p - \mathrm{onehot}(t)$$

$$\frac{d}{dx}\log x = \frac1x, \qquad \frac{d}{dx}e^x = e^x$$

## Matrix calculus

$$\frac{\partial}{\partial x}(Ax) = A, \qquad \frac{\partial}{\partial x}(x^{\top}Ax) = (A+A^{\top})x, \qquad \frac{\partial}{\partial X}\mathrm{tr}(AX) = A^{\top}$$

Rather than memorizing a table, use the rule from module 2: derive for one example where everything is two-dimensional, then fix the shapes by requiring that each gradient match its tensor.

## Taylor and optimization

$$f(x+\Delta) \approx f(x) + \nabla f^{\top}\Delta + \tfrac12\Delta^{\top}H\Delta$$

Gradient descent uses the first-order term. Newton's method uses the second and converges quadratically near a minimum — and is unusable at scale because $H$ is $n\times n$. Every practical second-order method (K-FAC, Shampoo, Adam's diagonal scaling) is a cheap approximation to that curvature information.

The precise framing, which is what a sharp interviewer probes for: Adam divides by $\sqrt{\hat v}$, an EMA of *squared gradients*, so it preconditions with the inverse square root of a **diagonal empirical Fisher** estimate — not with $H^{-1}$. It sits on the same axis as K-FAC and Shampoo, at the cheapest possible point on it. Saying "it is a very cheap diagonal preconditioner" is right; saying "it approximates the inverse Hessian" invites a correction.
