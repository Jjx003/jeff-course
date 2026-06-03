# Speculative decoding simulator

In the previous reading, speculative decoding was a systems pattern: a cheap
draft proposes several tokens, and the expensive target verifies them. In this
lab you will build a deliberately small estimator for that pattern.

The goal is not to reproduce vLLM, TensorRT-LLM, SGLang, or a research-grade
speculative sampler. The goal is to make the tradeoff numerically concrete. If
someone says "we draft eight tokens and get a 3x speedup," you should
immediately ask:

- How often are the proposed tokens accepted?
- How expensive is each drafted token?
- Does the target verification step really cost about one decode step?
- Is the win latency, throughput, or only a microbenchmark number?

Your function will estimate speedup from three inputs:

- `draft_length`: how many tokens the draft proposes,
- `acceptance`: the per-token acceptance probability,
- `draft_cost`: the cost of one drafted token measured in target-step units.

## Model to implement

Use this simplified model:

$$
\text{committed tokens} = 1 + \sum_{i=1}^{k} a^i
$$

$$
\text{cost} = 1 + kc_d
$$

$$
\text{speedup} =
\frac{\text{committed tokens}}{\text{cost}}
$$

where:

- $k$ is draft length,
- $a$ is acceptance probability,
- $c_d$ is draft cost per token measured in target-step units.

The `1` in committed tokens represents the target model's correction or fallback
token. The sum $\sum_{i=1}^{k} a^i$ represents the accepted draft prefix. Token
$i$ only commits when the first $i$ drafted tokens were all accepted.

## What to print

The starter file contains a fixed list of scenarios. Implement the estimator and
print each scenario using the requested formatting. Keep the output stable:
small formatting changes can fail the expected-output check even when the math
is right.

## Worked example

For `draft_length = 3`, `acceptance = 0.8`, and `draft_cost = 0.1`:

$$
\sum_{i=1}^{3} 0.8^i = 0.8 + 0.64 + 0.512 = 1.952
$$

The expected committed tokens are:

$$
1 + 1.952 = 2.952
$$

The cost is:

$$
1 + 3(0.1) = 1.3
$$

The speedup estimate is:

$$
\frac{2.952}{1.3} \approx 2.27
$$

That number is optimistic enough to be interesting, but it depends strongly on
acceptance staying high.

## What the model hides

This formula ignores batch effects, kernel launch overhead, target verification
details, cache paging, scheduler interactions, and the cost of computing the
target distribution used for exact sampling correction. That is intentional.

A production benchmark would report:

| Metric | Why it matters |
|---|---|
| time to first token | Interactive users feel startup latency. |
| inter-token latency | Decode smoothness depends on this. |
| accepted tokens per verification | The direct speculative gain. |
| GPU memory per request | Extra draft state can reduce concurrency. |
| p95 and p99 latency | Tail behavior can get worse even if averages improve. |

Your estimator is the whiteboard version. It teaches why acceptance rate and
draft cost dominate before you spend time on a full serving experiment.
