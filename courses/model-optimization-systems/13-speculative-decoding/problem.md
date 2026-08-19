# Speculative decoding and inference tricks

Autoregressive generation has an awkward shape for hardware. During prefill, the
model can process a whole prompt in parallel. During decode, the model usually
produces one token, appends that token to the context, and repeats. Token
$t + 1$ depends on token $t$, so the serving system cannot simply launch a
single large matrix multiplication for the whole answer.

That one-token-at-a-time loop is why interactive LLM serving feels different
from offline training. A user does not only care about total throughput. They
feel **time to first token** and **inter-token latency**. If each decode step
requires another pass through a very large target model, the user waits even
when the GPU is technically busy.

Speculative decoding is one of the most important tricks for attacking that
latency. The idea is simple enough to sound suspicious:

1. Use a cheap draft process to guess several future tokens.
2. Use the expensive target model to verify those guesses in one parallel step.
3. Commit the longest accepted prefix.
4. If a draft token is rejected, sample or choose a correction from the target.
5. Repeat from the new prefix.

The draft is never trusted as the final judge. It is a proposal mechanism. The
target model still defines the distribution you intend to serve.

![Ten lines of generated text, each one iteration of speculative decoding, with draft-proposed tokens in green, rejected tokens in red, and target corrections in blue](/courses/model-optimization-systems/specdec-fig1-accept-reject-trace.png)

*Figure 1 from Leviathan et al. (CC BY 4.0). Each line is one iteration, with a
6M-parameter draft proposing for a 97M-parameter target. Green tokens were
accepted, red were rejected, blue are the target's corrections. The whole
38-token sentence took 9 target passes instead of 38. Notice where the red
appears: at content words, where the small model has a real opinion and gets it
wrong. The connective tissue — punctuation, "index rose", "points" — is where a
tiny model is nearly as good as a large one, and that is the structure the
method monetizes.*

## The core tension

Suppose a draft model proposes $k$ tokens. The target model can evaluate the
prompt plus those $k$ draft tokens in a single forward pass, so verification is
parallel across the proposed positions. If most draft tokens are accepted, one
target pass can advance the sequence by several tokens. If most are rejected,
you paid extra draft cost and gained little.

This creates the central tradeoff:

| Quantity | Why it matters |
|---|---|
| Draft length $k$ | Larger $k$ gives more possible gain, but also more draft work and more wasted proposals after the first rejection. |
| Acceptance rate | The real engine of speedup. A fast draft that guesses poorly is not useful. |
| Draft cost | The draft must be cheap relative to target decode. A "small" model that burns another GPU can erase the win. |
| Verification cost | Target verification is not always exactly one ordinary decode step; kernels, cache layout, and batching matter. |
| Workload entropy | Low-entropy tasks such as boilerplate, code continuation, or constrained formats tend to be easier to draft. |

A good speculative system feels almost unfair: the target model keeps its
quality contract, while the serving loop commits multiple tokens per expensive
step. A bad speculative system adds complexity, memory pressure, and scheduler
fragility for a single-digit improvement.

## Why exact speculative sampling is possible

For greedy decoding, verification is intuitive: if the draft token equals the
target model's chosen token, accept it; otherwise replace it. Sampling is more
subtle because the target distribution may assign probability to many tokens.
The classic speculative sampling rule accepts a proposed token $x$ with a
probability derived from the ratio between target probability $p(x)$ and draft
probability $q(x)$:

$$
\alpha(x) = \min\left(1, \frac{p(x)}{q(x)}\right)
$$

If the token is rejected, the correction is sampled from the positive residual
distribution proportional to:

$$
\max(0, p(x) - q(x))
$$

The exact algorithm has more bookkeeping than this one-line summary, but the
lesson is important: speculative decoding is not merely "let a weaker model
write some tokens and hope." With the correct acceptance and correction rule,
the final samples can match the target model distribution.

### The proof, in five lines

This is one of the rare results in systems work whose correctness argument fits
on a napkin, and it is worth walking through, because the place where it works
is not where most people guess.

Let $X$ be the token the algorithm finally emits. There are two ways to emit a
particular $x$: propose it and accept it, or reject whatever was proposed and
draw $x$ from the residual. Take the first:

$$
\Pr[\text{propose } x \text{ and accept}]
= q(x)\cdot\min\!\left(1, \frac{p(x)}{q(x)}\right)
= \min\bigl(p(x),\, q(x)\bigr)
$$

Now the rejection probability, summing the complement over all tokens:

$$
\beta = 1 - \sum_{x'} \min\bigl(p(x'),\, q(x')\bigr)
$$

Here is the step that makes everything work. The normalizer of the residual
distribution is

$$
\sum_{x'} \max\bigl(0,\, p(x') - q(x')\bigr)
= \sum_{x'} \Bigl[p(x') - \min\bigl(p(x'), q(x')\bigr)\Bigr]
= 1 - \sum_{x'} \min\bigl(p(x'), q(x')\bigr) = \beta
$$

The residual's normalizer *is* the rejection probability. Not approximately —
identically, and for any $p$ and $q$. So the two factors cancel when we combine
the cases:

$$
\Pr[X = x] = \min\bigl(p(x), q(x)\bigr)
+ \beta \cdot \frac{\max\bigl(0, p(x)-q(x)\bigr)}{\beta}
= \min\bigl(p(x), q(x)\bigr) + \max\bigl(0, p(x)-q(x)\bigr)
$$

Check the two cases. If $p(x) \le q(x)$ the expression is $p(x) + 0$. If
$p(x) > q(x)$ it is $q(x) + p(x) - q(x)$. Either way:

$$
\Pr[X = x] = p(x) \qquad \blacksquare
$$

Read what the proof did and did not assume. It never used that $q$ is a good
approximation of $p$, that the draft model is smaller, that the two models share
a tokenizer, or anything at all about neural networks. **Any** proposal
distribution gives exactly the target distribution. A bad draft does not
introduce bias; it only wastes work. That asymmetry is why speculative decoding
is safe to deploy in a way that most approximate optimizations are not — the
failure mode is a slow server, never a different model.

### Acceptance rate is a distance, not a hyperparameter

The same algebra hands over the acceptance rate. The probability that a proposed
token survives is

$$
\alpha = \mathbb{E}_{x \sim q}\left[\min\!\left(1, \frac{p(x)}{q(x)}\right)\right]
= \sum_x \min\bigl(p(x), q(x)\bigr)
$$

and using $\min(a,b) = \tfrac{1}{2}(a + b - |a-b|)$ together with the fact that
both distributions sum to one:

$$
\alpha = \frac{1}{2}\left(1 + 1 - \sum_x |p(x)-q(x)|\right)
= 1 - \tfrac{1}{2}\lVert p - q\rVert_1
= 1 - D_{TV}(p, q)
$$

The acceptance rate is exactly one minus the **total variation distance**
between the target and the draft. This turns a quantity people usually measure
empirically into something with a definition: $\alpha = 1$ if and only if the
draft matches the target, $\alpha = 0$ only if their supports are disjoint, and
every intermediate value is a statement about distributional agreement at that
position.

It also reframes what draft training is for. Training a draft model is not
"making it good at language" — it is minimizing an expected total variation
distance to a specific target model on a specific traffic distribution. That is
why a draft distilled from the target beats a same-size model trained
independently, and why acceptance measured on one workload does not transfer to
another.

## Modern drafting families

By 2026, "speculative decoding" is more of a family than one algorithm.
Production stacks and inference libraries mix several proposal sources:

- **Separate draft model.** A smaller model trained or chosen to mimic the
  target. This is easy to reason about but adds weights, memory, and deployment
  coordination.
- **Self-speculative or early-exit decoding.** Intermediate layers propose
  tokens, later layers verify. This avoids a separate model but requires target
  architecture support.
- **EAGLE-style feature drafting.** A lightweight head predicts future hidden
  states or tokens from the target model's own features, often improving the
  speed-quality balance over a fully separate draft model.
- **Tree speculative decoding.** The draft proposes a small tree of candidates
  rather than one line. The target verifies many possible continuations, which
  can help under sampling or high uncertainty.
- **Prompt lookup and n-gram drafting.** For code, retrieval-augmented answers,
  transcripts, and repetitive documents, the next tokens are often copied from
  earlier context. A tiny non-neural draft can be surprisingly strong.
- **Schema-aware drafting.** For JSON, tool calls, SQL, or other constrained
  formats, the proposal source can use grammar knowledge so it does not waste
  guesses on invalid continuations.

The common pattern is proposal plus verification. The implementation details
are different because the bottlenecks are different.

## A worked intuition

Imagine a target model where one decode pass costs 1 unit. A draft model costs
0.08 units per token. You draft $k = 4$ tokens, and each drafted token is
accepted with probability $a = 0.8$ until the first rejection.

The expected number of accepted drafted tokens is approximated by:

$$
\sum_{i=1}^{4} a^i = 0.8 + 0.64 + 0.512 + 0.4096 = 2.3616
$$

If the target can also provide one fallback or correction token, the expected
committed tokens per target verification step are roughly:

$$
1 + 2.3616 = 3.3616
$$

The cost is:

$$
1 + 4(0.08) = 1.32
$$

So the rough speedup is:

$$
\frac{3.3616}{1.32} \approx 2.55
$$

This is not a complete serving simulator, but it explains why acceptance rate is
so powerful. If acceptance falls to $0.4$, the accepted-token sum becomes
$0.4 + 0.16 + 0.064 + 0.0256 = 0.6496$, and the same draft machinery is far less
attractive.

## Protein-model analogy

Protein folding and biomolecular prediction systems do not decode natural
language tokens in the same autoregressive loop. AlphaFold-style and
Boltz-style systems usually run encoders, pair representations, diffusion or
structure modules, confidence heads, and sometimes affinity heads. Still, the
systems instinct is familiar:

- use a cheap protein language model embedding before an expensive all-atom
  complex model,
- screen thousands of variants with a small model before folding the top
  candidates,
- run a coarse structure or confidence filter before docking or affinity
  prediction,
- generate many designs cheaply, then verify a small subset with AlphaFold3,
  Chai, Boltz, RFdiffusion-adjacent tooling, or physics-based refinement.

This course keeps returning to that pattern because it is the bridge between LLM
serving and computational biology: do not spend the most expensive model on
every possibility unless the cheap signal says the candidate deserves it.

## Recap

Speculative decoding is a latency optimization for autoregressive generation.
It wins when the accepted-token gain is larger than the draft overhead and the
serving system can exploit the extra parallelism. It fails when the draft is too
slow, acceptance is too low, memory pressure gets worse, or the workload is
already throughput-bound.

The next coding module implements the algorithm itself: a draft proposal, the
`min(1, p/q)` acceptance test, and the residual distribution that replacement
tokens are drawn from after a rejection. You will then verify the claim this
entire technique rests on — that speculative decoding does not change the output
distribution at all — both algebraically and by Monte Carlo. Along the way the
acceptance rate stops being a parameter you assume and becomes a quantity you
derive from the two distributions.
