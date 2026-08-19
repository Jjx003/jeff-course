# Implement speculative sampling and prove it is lossless

The reading gave you a speedup formula and one crucial claim it did not justify:
with the right acceptance rule, speculative decoding **does not change the
output distribution**. That claim is the entire reason the technique is
deployable. A 3x decode speedup that quietly shifts the model's sampling
distribution toward a 300M-parameter draft is not an optimization; it is a
silent model swap.

In this lab you implement the real algorithm and check that claim two ways: as
an exact algebraic identity over the vocabulary, and as a Monte Carlo experiment
over 200,000 draws. Then you go back to the reading's committed-token formula
and find out how well it actually holds up.

Notation follows the reading: $k$ is the draft length and $a$ is the marginal
probability that a drafted token is accepted. The code calls $a$ `alpha`, which
is the name used in the speculative-sampling papers. Draft cost $c_d$ does not
appear here — this module is about correctness and committed tokens, not the
cost model you already have.

Everything runs on CPU in float32 under `torch.manual_seed(0)`, so your Monte
Carlo numbers are the grader's Monte Carlo numbers. Wall-clock timing is printed
to **stderr**, which is streamed to you in the session log but is not graded.
The whole program should finish in about a second.

## The setup: two real modules, one vocabulary

You are given a `TinyLM`: an `nn.Embedding` followed by an `nn.Linear` over a
64-token vocabulary. It is a bigram model — the next-token logits depend only on
the last token — which means the full conditional distribution for every context
fits in one `(64, 64)` table. That table is the target distribution $p$.

The draft is the same model with all but the first `hidden` channels removed,
which is a crude version of what width pruning or distillation produces: a
smaller model that is genuinely correlated with the target and genuinely wrong.
A temperature knob sets how sharp the draft's distribution is. Two
configurations are used:

| Config | Draft hidden dim | Draft parameters | Character |
|---|---:|---:|---|
| strong draft | 48 | 6,208 | close to the target, high acceptance |
| weak draft | 2 | 320 | nearly uninformative, low acceptance |

Nothing is downloaded. The distributions come out of seeded modules, so they
have real structure — the target's next-token entropy is `1.9303` nats against
`4.1589` for a uniform 64-token vocabulary — rather than being hand-written
probability vectors chosen to make the math work.

## Part 1 — The acceptance rule

Implement three functions.

`acceptance_alpha(p, q)` returns

$$
a = \sum_t \min(p_t, q_t)
$$

`residual_distribution(p, q)` returns the distribution the target falls back to
after a rejection:

$$
p_{\text{res}}(t) = \frac{\max(0,\; p_t - q_t)}{\sum_s \max(0,\; p_s - q_s)}
$$

`speculative_sample(p, q, n)` runs the rule itself, $n$ times, vectorized:

1. the draft proposes $x \sim q$;
2. the target accepts with probability $\min\left(1, p_x / q_x\right)$;
3. on rejection, the emitted token is drawn from $p_{\text{res}}$, **not** from
   $p$.

Step 3 is the part that everyone gets wrong, and it is the part that makes the
scheme correct. The residual is where the target keeps the probability mass the
draft failed to cover. Replacing a rejected token with a fresh draw from $p$
looks reasonable, produces a perfectly valid probability distribution, and is
wrong. You will measure exactly how wrong.

Do not write a Python loop over trials. `torch.multinomial(q, n,
replacement=True)` draws all $n$ proposals at once, `torch.rand(n)` gives all
the accept/reject coins, and `torch.where` selects between proposals and
replacements. Drawing every replacement up front is legitimate because the
replacements are independent of the accept decisions.

## Part 2 — Prove it is lossless

This is the centerpiece, and it has two halves.

**The proof.** Implement `emitted_distribution(p, q)` as the literal law of the
sampler:

$$
\text{emitted}(t) = q_t \cdot \min\!\left(1, \frac{p_t}{q_t}\right)
\;+\; (1 - a)\, p_{\text{res}}(t)
$$

The first term is "the draft proposed $t$ and the target let it through". The
second is "something was rejected, and the residual draw landed on $t$". Write
it in that form rather than simplifying it to $\min(p_t, q_t)$ by hand — the
point is to check the *rule*, not to check an algebraic rewrite of the answer.
The program then verifies `torch.allclose(emitted, p)` and prints the maximum
absolute deviation. It comes out at float32 rounding: about `4.5e-08`.

Also implement `emitted_distribution_wrong`, which is the same expression with
$p$ substituted for $p_{\text{res}}$. It still sums to 1, which is precisely why
the bug survives casual testing, and its total variation distance from $p$ is
`0.1785` for the strong draft. That is not a rounding error. That is a different
model.

**The demonstration.** Run 200,000 speculative draws and 200,000 direct draws
from $p$, and compare the two empirical distributions with total variation
distance:

$$
\mathrm{TV}(u, v) = \tfrac{1}{2}\sum_t |u_t - v_t|
$$

You should see `TV(speculative, direct p samples)` around `0.0047` — pure Monte
Carlo noise at this sample size — while `TV(q, p)` sits at `0.2887`. The draft
is a genuinely poor approximation of the target, and the speculative output is
nonetheless correct. That contrast is the whole lesson.

The program also checks the identity $a = 1 - \mathrm{TV}(p, q)$, derived in
`theory.md`. Acceptance rate is not a mysterious empirical property of a model
pair; it is one minus the distance between their next-token distributions.

## Part 3 — Multi-token drafts and the reading's formula

Implement `simulate_draft_steps`, a real speculative step with $k = 8$:

- **Drafting.** Starting from a fixed context, the draft autoregressively
  proposes 8 tokens. It always produces all 8; verification is what truncates.
- **Verification.** The target scores every drafted position in parallel — this
  is the one expensive forward pass the whole technique is built around — and
  you then walk the positions in order, applying the same accept/reject test.
  One rejection kills every position after it.

Committed tokens per step is `accepted + 1`: whether the step ends in a
rejection (residual token) or survives all $k$ positions (bonus token from the
target), exactly one extra token is emitted.

The reading claimed

$$
E[\text{committed}] = 1 + \sum_{i=1}^{k} a^i
$$

which assumes acceptance events are independent and identically distributed
across positions. You now have the machinery to test that instead of asserting
it. Compare the measured mean against the prediction for $k \in \{2, 4, 8\}$ on
both draft configurations, and compare the measured prefix survival probability
at position $i$ against $a^i$.

The formula is wrong, in both directions, and the program prints the reason on
the line above: acceptance is context-dependent. For the strong draft, $a$
ranges from `0.3205` to `0.9639` across the 64 contexts, and the starting
context is an easy one at `0.7113` against a mean of `0.6165`, so the geometric
model *over*-predicts — by 13% at $k = 8$. For the weak draft the starting
context is harder than average, and the same formula *under*-predicts by 5%.
Read those tables carefully; the sign of the error is the interesting part.

Do not change the starter constants or the output labels. The grader checks
printed stdout.

## Recap

You have a speculative sampler that is provably distribution-preserving, an
exact algebraic certificate that the acceptance rule is correct, a measurement
of what the classic residual bug costs, and an honest assessment of how far the
reading's committed-token formula can be trusted. That closes the single-GPU
story — and opens the question the course has been deferring since module 2:
the 70B model every floor was computed for does not fit on one GPU at all. The
next module distributes it, and the roofline gains its final term:
communication.
