# A simple speedup model

Let:

- $k$ be the draft length,
- $a$ be the probability that a drafted token is accepted, assumed constant,
- $c_d$ be draft cost per token measured in target-step units,
- target verification cost be 1 unit.

If accepting token $i$ requires all previous draft tokens to have been accepted,
then the probability that token $i$ is committed is approximately $a^i$.
Therefore:

$$
E[\text{accepted draft tokens}] = \sum_{i=1}^{k} a^i
$$

If the target verification pass also yields one correction or fallback token,
the rough committed-token count is:

$$
E[\text{committed tokens}] = 1 + \sum_{i=1}^{k} a^i
$$

Draft cost is:

$$
\text{cost} = 1 + kc_d
$$

So the simplified speedup estimate is:

$$
\text{speedup} \approx
\frac{1 + \sum_{i=1}^{k} a^i}{1 + kc_d}
$$

When $a \ne 1$, the finite geometric sum is:

$$
\sum_{i=1}^{k} a^i = \frac{a(1-a^k)}{1-a}
$$

When $a = 1$, the sum is simply $k$.

The committed-token numerator collapses to a clean closed form. Adding the
guaranteed fallback token,

$$
1 + \sum_{i=1}^{k} a^i
= \frac{(1-a) + a(1-a^k)}{1-a}
= \frac{1 - a^{k+1}}{1-a},
$$

which is exactly the expected number of tokens committed per verification step
derived in the original speculative-decoding analysis (Leviathan et al.). As
$k \to \infty$ with $a < 1$ it saturates at $1/(1-a)$: no matter how long the
draft, a constant per-token rejection probability caps the average advance. That
ceiling is why draft length has diminishing returns and is usually tuned, not
maximized.

![Chart of expected tokens generated per iteration against acceptance rate alpha, for draft lengths gamma of 1, 3, 5, 7, and infinity](/courses/model-optimization-systems/specdec-fig2-expected-tokens.png)

*Figure 2 from Leviathan et al. (CC BY 4.0), plotting the same closed form. The
spread between the $\gamma$ curves is what matters: at $\alpha = 0.6$ the
curves for $\gamma = 5$, $7$, and $\infty$ are nearly on top of each other, so
drafting past 5 buys almost nothing. At $\alpha = 0.9$ they separate sharply
and long drafts pay. Draft length should track acceptance, and the chart shows
by roughly how much.*

## Why the first rejection matters

Speculative verification accepts a prefix. If the first three draft tokens are
accepted and the fourth is rejected, tokens after the fourth cannot be trusted
under that branch. They were conditioned on a token the target did not accept.
This is why the model uses $a^i$ rather than $ka$.

For $k = 4$ and $a = 0.75$:

| Token position | Commit probability |
|---|---:|
| 1 | $0.75$ |
| 2 | $0.75^2 = 0.5625$ |
| 3 | $0.75^3 = 0.421875$ |
| 4 | $0.75^4 = 0.31640625$ |

The fourth token can be individually "good" with probability $0.75$, but it
only reaches the output if the first, second, and third draft tokens were also
accepted.

## What the formula hides

The simplified estimator is intentionally clean. Real serving systems have more
moving parts:

- **KV-cache behavior.** Draft and target may each need cache space. If adding a
  draft model reduces batch size or causes cache paging, the theoretical win
  can vanish.
- **Verification kernels.** Verifying $k$ positions is not always identical to a
  normal prefill or decode step. Attention shape, cache reads, and logits
  extraction affect latency.
- **Scheduler effects.** Continuous batching systems already mix requests at
  token granularity. Speculative decoding changes how many tokens a request may
  commit per scheduler iteration.
- **Sampling temperature.** Discussed on its own below, because the usual
  intuition about it is backwards.
- **Domain skew.** Acceptance may be high for code boilerplate and low for
  creative writing, even with the same model pair.
- **Tail latency.** Average speedup is not enough. If occasional low-acceptance
  requests monopolize memory or queue slots, p95 latency can get worse.

This does not make the formula useless. It makes the formula a first pass:
enough to reject bad ideas early, not enough to certify a deployment.

## Temperature does not do what people say it does

The received wisdom is that higher temperature lowers acceptance, because more
continuations become plausible. The identity $\alpha = 1 - D_{TV}(p, q)$ from
the reading says otherwise, and it is worth following the argument because it
changes what you tune.

Temperature is applied to *both* models. As $T$ grows, $p_T$ and $q_T$ both
flatten toward the uniform distribution, so the distance between them shrinks
and $\alpha$ rises. In the limit $T \to \infty$ both are uniform, $D_{TV} = 0$,
and $\alpha \to 1$. At the other end, as $T \to 0$ both collapse onto their
argmax, and $\alpha$ becomes the indicator that the two models agree on the top
token — so averaged over positions, $\alpha(T\!\to\!0)$ is exactly the **top-1
agreement rate** of the model pair.

Simulating a correlated target/draft pair over a 32k vocabulary makes the shape
concrete:

| Temperature | $\alpha = 1 - D_{TV}$ |
|---:|---:|
| $\to 0$ | 0.559 (= top-1 agreement, measured at 0.560) |
| 0.5 | 0.613 |
| 1.0 | 0.693 |
| 2.0 | 0.824 |
| 5.0 | 0.929 |

Acceptance rises monotonically with temperature, and the $T \to 0$ value lands
on the top-1 agreement rate to three decimals, as the theory requires.

So where does the folk claim come from? Two places, and both are real effects
that simply are not temperature.

*Confusing two algorithms.* With greedy decoding people typically use the
equality check — accept if the draft token equals the target's argmax — which is
a different rule from $\min(1, p/q)$. Moving from greedy-with-equality to
sampling-with-the-ratio-rule does often lower measured acceptance. That is a
change of algorithm, and attributing it to temperature is a category error.

*Truncation, not temperature.* Top-$k$ and top-$p$ are usually applied
alongside temperature and they behave completely differently. Truncation makes
$p$ and $q$ **sparse**, and a token inside $q$'s nucleus but outside $p$'s has
$p(x) = 0$, so it is rejected with certainty. Two models rarely agree on their
nucleus boundaries, so top-$p$ can cut $\alpha$ hard even as raising $T$ alone
would have increased it. If acceptance drops when you "raise temperature," check
whether you also widened the truncation set — that is the more likely culprit,
and it is the knob to investigate.

The general habit is the one this course keeps returning to: when a system has a
closed-form model, use it to check the folklore rather than the other way around.

## Choosing a draft length

The best $k$ is rarely a universal constant. Larger $k$ increases possible
tokens per verification step, but the marginal probability $a^i$ shrinks. The
fifth drafted token may be cheap, but it is only useful when the first four were
accepted.

Setting $\partial(\text{speedup})/\partial k = 0$ on the closed form above, with
$L = -\ln a > 0$, gives the first-order condition

$$
a^{k+1}\bigl[L(1 + kc_d) + c_d\bigr] = c_d
$$

This is transcendental and has no clean closed-form root, which is itself
informative — there is no memorable formula for the best draft length, so the
practical answer is to compute it or adapt to it.

![Two-panel chart: expected speedup against draft length for several acceptance rates with the maximizing k marked, and the maximizing k against acceptance rate for three draft costs](/courses/model-optimization-systems/specdec-optimal-k.svg)

Three things in that picture are worth internalizing. The optimum is **interior**
— overshooting $k$ costs you real throughput, because you pay for every drafted
token whether or not it survives. The optimum **moves a long way** with
acceptance: from $k = 3$ at $\alpha = 0.5$ to $k = 11$ at $\alpha = 0.9$, so a
single tuned constant is wrong for most of your traffic. And the peaks are
**flat**, which is the saving grace: being off by two or three is nearly free,
so an adaptive controller that tracks the recent acceptance rate captures almost
all of the available gain without any search.

A serving stack can choose $k$ dynamically using signals such as:

- recent acceptance rate for the request,
- prompt or route type,
- temperature and top-p settings,
- available GPU memory,
- active batch size,
- target model size,
- whether grammar constraints are active.

In practice, dynamic control matters because speculative decoding is a systems
feature, not a pure model feature. The same model pair can behave differently on
chat, code, JSON extraction, retrieval-grounded summarization, and protein
sequence annotation.

## Where the geometric model stops applying

Everything above assumes a **linear** draft: one chain of $k$ tokens, accepted
as a prefix, with a constant per-token acceptance probability. Both assumptions
are approximations, and the two main modern refinements break them deliberately.

**Tree drafting.** Instead of one chain, propose a tree of candidate
continuations and verify all of them in a single target pass, using an attention
mask that encodes the tree structure so each node attends only to its ancestors.
The target now evaluates many possible futures for roughly the cost of one long
sequence, and the committed path is the deepest accepted root-to-node path.
Expected accepted length rises for the same number of target passes. The
geometric formula no longer applies — the answer depends on the tree's shape,
and choosing that shape (wide and shallow for high-entropy positions, narrow and
deep for low-entropy ones) becomes the tuning problem that $k$ used to be.

**Drafting in feature space.** EAGLE's observation is that token sequences are a
bad thing to predict and hidden-state sequences are a much better one: features
evolve smoothly where tokens jump discretely. So the draft head predicts the
target model's own second-to-top-layer hidden state for the next position, then
runs it through the *target's* LM head to get a token distribution. Two
consequences follow. The draft is tiny, because it reuses the target's
embedding and output layers rather than learning its own. And it is
better-conditioned, because the regularity it exploits is real. EAGLE also
resolves the ambiguity that pure feature prediction leaves — a feature vector
under-determines the next token — by conditioning on the token actually sampled
one step ahead.

Neither changes the correctness argument. The proof in the reading placed no
constraint whatsoever on where proposals come from, so a tree, a feature-space
head, an n-gram table scraped from the prompt, or a grammar-constrained
generator are all admissible drafts. This is the practical payoff of a theorem
with weak hypotheses: the proposal mechanism became a free design space, and the
last few years of work in this area have been people exploring it.

| Draft source | Extra weights | Where it wins |
|---|---|---|
| separate small model | a full second model | general traffic, easy to reason about |
| self-speculation / early exit | none | when the target supports it architecturally |
| EAGLE-style feature head | small head, reuses target embeddings | best acceptance per parameter |
| tree drafting | orthogonal to the above | high-entropy sampling, uncertain positions |
| prompt lookup / n-gram | none at all | summarization, RAG, code edits, any copying task |
| grammar-aware | none | JSON, tool calls, SQL, constrained formats |

The last row deserves a note, because it is the cheapest win on this list and
the most often skipped. When output must satisfy a grammar, large stretches of it
are *determined* — the closing brace, the quote after a key, the comma. A draft
that knows the grammar proposes those with certainty and gets them accepted with
certainty. No model required, and $\alpha$ near 1 on exactly the tokens a neural
draft would have wasted a forward pass on.

## A biological systems analogy

In protein modeling, the analogous formula is not about accepted tokens. It is
about candidate funnels. Suppose a cheap screen costs $c_s$ per sequence and an
expensive structure or affinity model costs 1 unit per sequence. If the screen
retains fraction $r$ of candidates while preserving most true positives, the
rough cost per original candidate is:

$$
c_s + r
$$

The gain over running the expensive model on everything is about:

$$
\frac{1}{c_s + r}
$$

This is not speculative decoding, but it shares the same warning. A cheap screen
that is not cheap enough, or that filters out the biological signal you care
about, is not an optimization. It is a way to get wrong answers faster.

## Going deeper

- Fast Inference from Transformers via Speculative Decoding: https://arxiv.org/abs/2211.17192
- Accelerating Large Language Model Decoding with Speculative Sampling: https://arxiv.org/abs/2302.01318
- EAGLE speculative sampling: https://arxiv.org/abs/2401.15077
- TensorRT-LLM speculative decoding examples: https://developer.nvidia.com/blog/boost-llama-3-3-70b-inference-throughput-3x-with-nvidia-tensorrt-llm-speculative-decoding/
- Medusa, multiple decoding heads with tree attention: https://arxiv.org/abs/2401.10774
- SpecInfer, tree-based speculative inference and verification: https://arxiv.org/abs/2305.09781
- Prompt lookup decoding, an n-gram draft with no model at all: https://github.com/apoorvumang/prompt-lookup-decoding
- vLLM documentation on speculative decoding: https://docs.vllm.ai/en/latest/features/spec_decode.html
