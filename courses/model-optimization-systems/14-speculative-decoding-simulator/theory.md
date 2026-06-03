# Why this tiny simulator is useful

The most useful performance models are often the ones you can hold in your
head. This lab's simulator is intentionally small enough to compute by hand, but
it still captures the two forces that decide whether speculative decoding is
worth trying:

1. accepted tokens per target verification step,
2. extra work spent on the draft.

If the first force is larger than the second, speculative decoding can help. If
not, the algorithm may be elegant but the system will disappoint.

## Prefix acceptance

The key detail is prefix acceptance. Suppose the draft proposes:

```text
the protein binds strongly
```

If the target model rejects `binds`, then `strongly` is no longer a valid
continuation of the target-approved prefix. It was proposed under a branch that
the target did not accept. That is why the estimator uses:

$$
a + a^2 + a^3 + \cdots + a^k
$$

rather than:

$$
ka
$$

The difference is small when $a$ is near 1 and large when $a$ is modest.

## Marginal value of another draft token

The marginal value of drafting token $i$ is roughly $a^i$. If $a = 0.9$, the
sixth token has probability:

$$
0.9^6 \approx 0.53
$$

That is still worth considering. If $a = 0.5$, the sixth token has probability:

$$
0.5^6 = 0.015625
$$

That is almost certainly not worth much draft cost. This is why real systems
often tune draft length dynamically.

## Interpreting the scenarios

When you run the starter scenarios, compare them along three axes:

- Same draft length, different acceptance.
- Same acceptance, different draft cost.
- Same draft cost, different draft length.

You should see that longer drafts only help when acceptance remains high and
draft cost remains low. A long draft with mediocre acceptance can look worse
than a short draft because most of the tail tokens are thrown away after an
early rejection.

## Relation to biological screening

This lab is about language decoding, but the habit transfers directly to protein
modeling. A common 2026 workflow is not "run the most expensive biomolecular
model on every sequence." It is closer to:

1. embed or score many sequences with a protein language model,
2. filter variants or complexes using a cheap criterion,
3. fold or co-fold the promising subset with an all-atom model,
4. use confidence, interface, or affinity signals to decide what deserves lab
   attention.

That pipeline has the same shape as speculative decoding: cheap proposal,
expensive verification. The equations differ, but the discipline is the same.
Measure the cheap stage, measure the retained fraction, and be honest about
false negatives.

## Limits of the abstraction

The simulator treats target verification as cost 1 regardless of $k$. In a real
implementation, verifying several positions changes tensor shapes and may use a
different kernel path from ordinary single-token decode. Some target models
verify draft trees rather than a single chain. Some deployments use grammar
constraints, prompt lookup, or self-speculative heads. Some systems care more
about time-to-first-token than steady decode.

Those complexities are real, but they do not remove the value of this toy
calculation. They tell you what to measure next.
