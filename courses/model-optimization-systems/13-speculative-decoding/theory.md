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
- **Sampling temperature.** Higher entropy lowers acceptance because many
  continuations are plausible. Greedy, deterministic, and constrained workloads
  are easier.
- **Domain skew.** Acceptance may be high for code boilerplate and low for
  creative writing, even with the same model pair.
- **Tail latency.** Average speedup is not enough. If occasional low-acceptance
  requests monopolize memory or queue slots, p95 latency can get worse.

This does not make the formula useless. It makes the formula a first pass:
enough to reject bad ideas early, not enough to certify a deployment.

## Choosing a draft length

The best $k$ is rarely a universal constant. Larger $k$ increases possible
tokens per verification step, but the marginal probability $a^i$ shrinks. The
fifth drafted token may be cheap, but it is only useful when the first four were
accepted.

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
