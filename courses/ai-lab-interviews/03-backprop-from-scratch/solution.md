# Walkthrough

## forward

The only decision worth thinking about is what to cache. You need `x` for `dW1`, `z1` for the ReLU mask, `h1` for `dW2`, and the softmax probabilities for `dz2`. Caching `probs` rather than `z2` means backward never exponentiates anything — the numerically delicate part happens exactly once, in `log_softmax`.

Computing the loss from `log_softmax` output rather than from `log(softmax(z))` is the point of the whole stability discussion: gathering `logp[arange(n), y]` never materializes a tiny probability that then has to be logged.

## backward

Four lines of real content and three lines of bookkeeping. The subtlety is entirely in the `/ n`.

The loss is a *mean* over the batch, so the chain rule contributes a factor of `1/N` once. Folding it into `dz2` immediately means every subsequent gradient inherits it automatically. The alternative — dividing at the end, in four separate places — works, and is where people forget one.

The ReLU backward is `dh1 * (z1 > 0)`. Note it gates on `z1`, the pre-activation, not on `h1`. They agree here because ReLU output is zero exactly where the input was negative, but on an activation where that is not true, gating on the wrong tensor is silently wrong.

## numerical_gradient

The two things people get wrong under time pressure:

**Restoring the original value.** If you perturb, evaluate, and move on without restoring, every subsequent entry is computed against a model that has drifted. The errors are small enough that the check still roughly passes, which makes this genuinely hard to spot.

**Using a flat view.** `params[name].reshape(-1)` returns a view sharing memory with the original array, so writing through it mutates the actual parameter. That is what lets one loop handle both `(D, H)` matrices and `(H,)` vectors without branching on rank.

## relative_error

$$\frac{|a-b|}{\max(|a|+|b|, \varepsilon)}$$

The `eps` floor matters: `b2` starts at zero and its gradient can be genuinely tiny, so a bare denominator can be zero.

## Why the tolerances are what they are

`1e-7` for finite differences: in float64 with a central difference at `h = 1e-5`, truncation error is $O(h^2) = 10^{-10}$ and roundoff is roughly $\varepsilon/h \approx 10^{-11}$. Landing near `1e-9` is normal; `1e-7` is a comfortable ceiling that still fails loudly on a real bug.

`1e-10` for autograd: both computations are float64 doing the same arithmetic in a slightly different order, so they agree to near machine precision. A looser threshold here would let a genuine convention mismatch through.

## The follow-up you should expect

> "Finite differences take `O(P)` forward passes. What would you do on a real model?"

Check a random slice of parameters rather than all of them; use a tiny model with the same code path; or test each layer's backward in isolation against autograd. In production the answer is usually: rely on autograd, and reserve hand-written backward passes for custom kernels — where you then test the kernel against a slow reference implementation, not against finite differences.
