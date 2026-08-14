# Solution walkthrough

## The residual is the whole algorithm

Strip away the systems framing and speculative sampling is four lines: propose
from $q$, accept with probability $\min(1, p/q)$, otherwise draw from
$\max(0, p - q)$ normalized, emit. Three of those four lines are obvious. The
fourth is the theorem.

The reason it works is a cancellation that the code makes visible. The residual
normalizer is

$$
Z = \sum_t \max(0,\, p_t - q_t) = \sum_t p_t - \sum_t \min(p_t, q_t) = 1 - a
$$

and the probability of taking the rejection branch at all is also $1 - a$. So
the two factors cancel, and the rejection path contributes exactly
$\max(0, p_t - q_t)$ to the emitted distribution. The acceptance path contributes
$\min(p_t, q_t)$. Their sum is $p_t$, identically, for every token.

That cancellation is not something you would guess. It is why the exercise makes
you build `emitted_distribution` out of the rule rather than out of
`torch.minimum` — writing $q \cdot \min(1, p/q)$ keeps the structure of the
sampler in the expression, so the `allclose` is a test of the algorithm and not a
restatement of the conclusion.

## Why the wrong version is so hard to catch

`emitted_distribution_wrong` sums to 1. That is the trap. Every cheap invariant
you would think to assert — non-negative, normalized, right shape, right dtype —
passes. Nothing crashes. The generated text is fluent. The acceptance rate and
the speedup are unchanged, because the bug lives entirely in what happens after
a rejection.

What you have actually built is

$$
a\,m + (1-a)\,p, \qquad m = \frac{\min(p, q)}{a}
$$

a mixture of the target with the normalized $p$-$q$ overlap, which is tilted
toward the draft. It over-emits tokens the draft already likes and under-emits
tokens the draft misses. In the exercise this lands `0.1785` and `0.1319` in
total variation from the target, against `0.0047` of Monte Carlo noise in the
correct sampler — roughly forty times the noise floor. In production it means
your 7B draft's preferences are now visible in your 70B model's output, and the
only way you would find out is an eval regression you cannot explain.

The exact form $\mathrm{TV}(\text{wrong}, p) = a \cdot \mathrm{TV}(m, p)$ also
explains why you cannot dodge it by choosing a better or worse draft. The
corruption goes to zero only in the two useless limits: a perfect draft
(nothing is ever rejected) or a hopeless one (the fallback is essentially always
taken, and the fallback is a plain draw from $p$). Everywhere in between — every
regime where speculative decoding is worth deploying — it is real.

## Two proofs beat one

The module checks correctness twice on purpose, and the two checks fail in
different ways.

The **algebraic identity** is exact and instantaneous. It has no sampling noise,
so it catches sign errors, missing clamps, and wrong normalizers with zero
ambiguity: `max |emitted - p|` is either float32 rounding at `4.5e-08` or it is
not. What it cannot catch is a sampler that does not implement the rule you
wrote down — a wrong `torch.where` polarity, a reversed comparison, a `multinomial`
call on the wrong tensor.

The **Monte Carlo run** catches exactly those, because it exercises the actual
sampling path. What it cannot do is be precise: at 200,000 draws over a 64-token
vocabulary, two empirical distributions from the *same* law differ by about
`0.005` in total variation, so it cannot distinguish "correct" from "wrong by
0.001". It would, however, immediately flag the residual bug at `0.13`.

Together they cover the space. This is the general shape of testing a sampler:
verify the law algebraically where you can, and verify that your code implements
the law by sampling from it.

## The committed-token tables are the payoff

The reading asserted $E[\text{committed}] = 1 + \sum_{i=1}^{k} a^i$. This module
derives where that comes from and where it breaks.

The exact statement needs no assumptions at all. The number of accepted draft
tokens is $\sum_i \mathbf{1}[S_i]$ where $S_i$ is "the first $i$ all survived",
so linearity of expectation gives

$$
E[\text{committed}] = 1 + \sum_{i=1}^{k} \Pr[S_i]
$$

The reading's version substitutes $\Pr[S_i] = a^i$. That substitution is the
approximation, and it requires acceptance to be independent and identical across
positions. Neither holds.

The measurements show the failure with a sign that flips between configurations:

| Config | $a$ at start | mean $a$ over contexts | $k = 8$ measured | $k = 8$ formula |
|---|---:|---:|---:|---:|
| strong | 0.7113 | 0.6165 | 2.8703 | 3.3023 |
| weak | 0.2283 | 0.3649 | 1.3584 | 1.2959 |

Acceptance is a property of a *context*, not of a model pair. The strong draft's
per-context $a$ spans `0.3205` to `0.9639`. Start from an easy context and the
draft's later positions regress toward the mean, so extrapolating $a^i$
overshoots — by 13% at $k = 8$. Start from a hard one, as the weak draft does,
and the same formula undershoots.

The honest conclusion is not "the formula is wrong." It is that a single scalar
acceptance rate is a summary statistic of a distribution, and raising it to the
eighth power amplifies whatever the summary threw away. Use the formula to
decide whether speculative decoding is worth trying. Use measured committed
tokens per step to decide what $k$ to ship.

## What carries forward

Three things survive contact with a real serving stack:

1. **Correctness is free and non-negotiable.** The proof holds for any draft. If
   a speculative implementation changes your outputs, it has a bug, not a
   tradeoff.
2. **Acceptance is distance.** $a = 1 - \mathrm{TV}(p, q)$ means every technique
   for improving acceptance — distillation, shared tokenizers, EAGLE-style
   feature drafting, lower temperature, grammar constraints — is a technique for
   moving $q$ toward $p$. There is no other mechanism.
3. **Per-step gain is measured, not derived.** Context-dependence, tree drafting,
   batching, and cache pressure all break the closed form. The formula sets your
   expectations; the harness sets your configuration.
