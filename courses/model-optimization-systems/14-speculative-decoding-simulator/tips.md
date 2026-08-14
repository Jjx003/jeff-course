# Hints

Work in TODO order. TODOs 1 through 4 are pure algebra on 64-element tensors and
have no randomness in them at all — get `allclose(emitted, p): True` printing
before you touch the Monte Carlo code. If the exact identity fails, no amount of
sampling will save you.

## TODO 1 and 2 — alpha and the residual

Both are one-liners, and they are secretly the same quantity twice:

```python
alpha = float(torch.minimum(p, q).sum())

residual = torch.clamp(p - q, min=0.0)
p_res = residual / residual.sum()
```

`residual.sum()` is exactly `1 - alpha`. You do not have to use that fact — just
normalize by the sum — but noticing it is what makes the correctness proof click.

## TODO 3 — the exact identity

Write it in the shape the docstring gives, not in its simplified form:

```python
accept_prob = torch.clamp(p / q, max=1.0)          # min(1, p/q)
emitted = q * accept_prob + (1.0 - alpha) * p_res
```

You may notice that `q * torch.clamp(p / q, max=1.0)` is just
`torch.minimum(p, q)`. It is, and that identity is a step in the proof — but if
you write `torch.minimum(p, q)` here you are no longer testing the acceptance
rule, you are testing an algebraic rearrangement of the answer you already
believe. Keep the ratio form. The check should be able to fail.

## TODO 4 — the bug, on purpose

Same expression, with `p` where `p_res` was:

```python
wrong = q * accept_prob + (1.0 - alpha) * p
```

Watch what it prints. It sums to 1, it looks like a distribution, and its total
variation distance from the target is around `0.13` to `0.18`. Compare that to
the `0.0047` of Monte Carlo noise in the correct sampler.

## TODO 5 — vectorizing the sampler

`torch.multinomial(q, n, replacement=True)` accepts `n` far larger than the
vocabulary size when `replacement=True`, so all 200,000 proposals come out of
one call:

```python
proposal = torch.multinomial(q, n, replacement=True)      # (n,)
u = torch.rand(n)
accepted = u < (p[proposal] / q[proposal])
replacement = torch.multinomial(p_res, n, replacement=True)
tokens = torch.where(accepted, proposal, replacement)
```

`p[proposal]` is advanced indexing: it gathers the target probability of every
proposed token in one shot.

The `min(1, ·)` from the rule is missing on purpose. Since `u` is uniform on
$[0, 1)$, `u < p/q` and `u < min(1, p/q)` are the same event — when the ratio
exceeds 1 the test passes either way. Leaving the clamp out is fine here; leaving
it out of `emitted_distribution` is not, because there you are evaluating the
probability itself rather than comparing it to a uniform.

Drawing every replacement up front and discarding most of them is deliberate. It
costs one extra `multinomial` call and keeps the whole thing branch-free, and it
is valid because the replacement draw is independent of the accept decision.

## TODO 6 — the multi-token step

Two phases, and the order matters.

**Drafting.** The draft runs autoregressively on its own output. It always
produces all `draft_len` tokens — it has no idea which ones will survive:

```python
context = torch.full((n,), context_token, dtype=torch.long)
for _ in range(draft_len):
    contexts.append(context)
    context = torch.multinomial(q_table[context], 1).squeeze(1)
    proposals.append(context)
```

`q_table[context]` is a `(n, VOCAB)` gather of per-lane distributions, and
`torch.multinomial` handles a batch of rows directly.

**Verification.** Now walk the positions in order with an `alive` mask that can
only ever turn off:

```python
index = proposals[i].unsqueeze(1)
p_x = p_table[contexts[i]].gather(1, index).squeeze(1)
q_x = q_table[contexts[i]].gather(1, index).squeeze(1)
alive = alive & (torch.rand(n) < p_x / q_x)
accepted += alive.long()
```

Writing `alive = torch.rand(n) < p_x / q_x` without the `&` is the bug that
turns prefix acceptance into independent per-position acceptance, and it will
inflate your committed-token counts.

Committed tokens is `accepted + 1` unconditionally: a rejected step emits one
residual token, and a fully accepted step emits one bonus token from the target's
distribution after the last draft token. Either way, exactly one.

You only need to run the simulator once, at `MAX_DRAFT = 8`. A $k = 2$ step is a
truncation of the same process, so `counts.clamp(max=2)` gives the $k = 2$
statistics from the $k = 8$ run — the draft's behavior at positions 1 and 2 does
not depend on how many more tokens it went on to propose.

## Common mistakes

- **Sampling the rejection replacement from `p` instead of `p_res`.** This is
  the big one, and it is the whole reason the module exists. The result is still
  a valid probability distribution — it sums to 1 — so nothing crashes and no
  assertion fires. What you have built is a sampler that emits
  $a \cdot m + (1-a) \cdot p$, where $m$ is the normalized $\min(p, q)$ overlap.
  That mixture is pulled toward the draft, over-emitting tokens the draft likes
  and under-emitting tokens it misses. You get your speedup and you quietly serve
  a different model. `emitted_distribution_wrong` exists so you can see the size
  of it.
- Normalizing the residual by `p.sum() - q.sum()` (which is 0) instead of by the
  sum of the clamped difference.
- Forgetting `torch.clamp(..., min=0.0)` before normalizing, which leaves
  negative "probabilities" and a normalizer that is wrong.
- Using `alive = ...` instead of `alive = alive & ...` in the verification loop.
- Letting the draft stop at the first rejection. Real drafting is speculative in
  both senses: all $k$ tokens are produced before any of them is judged.
- Verifying position $i$ against `p_table[proposals[i]]` instead of
  `p_table[contexts[i]]` — an off-by-one that scores each token against the
  distribution it induces rather than the one that produced it.
- Comparing distributions with mean squared error instead of total variation.
  TV has a meaning here: it is $1 - a$, and it bounds the probability that any
  event is judged differently under the two distributions.
- Looping over trials in Python. 200,000 iterations of a scalar `multinomial`
  turns a half-second program into a several-minute one.

## Sanity checks

Concrete values from a correct run:

- `p entropy: 1.9303` nats against `4.1589` for a uniform 64-token vocabulary.
  If yours is near 4.16, you dropped the temperature division.
- `alpha == 1 - TV(p, q): True` for both configurations. This is exact algebra,
  not a measurement — if it is `False`, one of `acceptance_alpha` or
  `total_variation` is wrong, and the factor of $\tfrac{1}{2}$ in TV is the usual
  culprit.
- `max |emitted - p|: 0.000000` and `allclose(emitted, p): True`. The true
  deviation is about `4.5e-08`, which is float32 rounding on a 64-element sum.
  The `[measured]` line on stderr prints it in full.
- Strong draft: `alpha: 0.7113`, empirical acceptance `0.7115`. Those should
  agree to about three decimals at 200,000 trials.
- Weak draft: `alpha: 0.2283`, empirical acceptance `0.2280`.
- `TV(speculative, direct p samples)` around `0.0044` to `0.0047` for both
  configurations, against `TV(q, p)` of `0.2887` and `0.7717`. A 60-fold and
  170-fold gap respectively: the drafts are bad, the outputs are not.
- Prefix survival at $i = 1$ must match `alpha` to within Monte Carlo noise
  (`0.7101` vs `0.7113`). If position 1 is off, the acceptance test itself is
  wrong and nothing downstream is meaningful.

If `TV(speculative, direct p samples)` comes out around `0.05` rather than
`0.005`, you are almost certainly sampling replacements from `p`. If it comes
out near `TV(q, p)`, you are emitting the proposal unconditionally.

## Reading the committed-token tables

This is the part that pays back the reading module, so do not skim it.

| Config | $a$ | $k$ | Measured | Formula | Error |
|---|---:|---:|---:|---:|---:|
| strong | 0.7113 | 2 | 2.1618 | 2.2172 | −2.5% |
| strong | 0.7113 | 4 | 2.6281 | 2.8331 | −7.2% |
| strong | 0.7113 | 8 | 2.8703 | 3.3023 | −13.1% |
| weak | 0.2283 | 2 | 1.3112 | 1.2805 | +2.4% |
| weak | 0.2283 | 4 | 1.3524 | 1.2951 | +4.4% |
| weak | 0.2283 | 8 | 1.3584 | 1.2959 | +4.8% |

Two things to take from this.

The error **grows with $k$**, in both directions, because $a^i$ compounds an
error that the first position does not have. At $k = 2$ the formula is good to a
few percent; at $k = 8$ it is off by 13% for the strong draft.

The **sign differs by configuration**, and the explanation is printed one section
above the table: acceptance is a property of the context. For the strong draft,
$a$ across the 64 contexts runs from `0.3205` to `0.9639` with a mean of
`0.6165`, and the starting context sits at `0.7113` — easier than typical, so
later positions regress downward and the geometric extrapolation overshoots. For
the weak draft the starting context is `0.2283` against a mean of `0.3649` —
harder than typical, so the formula undershoots.

The practical lesson: measuring $a$ on one prompt and extrapolating to $k = 8$
gives you a number that can be wrong by more than 10% in either direction.
Measure committed tokens per step directly.

## Going deeper

Things worth trying after the grader passes:

- Set both configs to the same `hidden` and sweep `temperature` from `0.05` to
  `2.0`. Plot `alpha` against draft temperature and confirm it tracks
  $1 - \mathrm{TV}(p, q)$ at every point.
- Sharpen the *target* by lowering `TARGET_TEMP`. Acceptance rises for a
  well-matched draft and collapses for a mismatched one — the standard
  observation that greedy and low-temperature decoding are easier to speculate on.
- Compute `TV(wrong, p)` as `alpha * TV(min(p,q)/alpha, p)` and confirm it
  matches the direct computation, then sweep a family such as
  `q = (1 - w) * p + w * uniform` and watch the corruption vanish at both
  $a \to 1$ and $a \to 0$ while peaking in between.
- Replace the fixed `CONTEXT_TOKEN` with a random starting context per step and
  re-measure committed tokens. Averaging over contexts moves the measurement
  toward the mean-$a$ prediction and shrinks the sign asymmetry.
- Implement tree drafting: propose two candidates at each position instead of
  one, verify both, and commit the longest surviving branch. The geometric
  formula stops applying entirely, which is the point.

## References

- Leviathan, Kalman, and Matias, *Fast Inference from Transformers via
  Speculative Decoding* (ICML 2023, arXiv 2211.17192) — introduces the
  accept/reject rule and proves the emitted distribution equals the target's.
- Chen, Borgeaud, Irving, Lespiau, Sifre, and Jumper, *Accelerating Large
  Language Model Decoding with Speculative Sampling* (arXiv 2302.01318, 2023) —
  the concurrent formulation, with the modified-rejection-sampling proof written
  out for the multi-token case.
- Li, Wei, Zhang, and Zhang, *EAGLE: Speculative Sampling Requires Rethinking
  Feature Uncertainty* (ICML 2024, arXiv 2401.15077) — drafts in the target's
  own feature space instead of using a separate model.
