# Stable Softmax Operations

Five functions, none longer than seven lines, and all of them are asked about.

The online softmax recurrence in particular is a favourite: it is the mathematical core of FlashAttention, it is derivable on a whiteboard in two minutes, and it separates people who have read the FlashAttention abstract from people who have read the paper.

## What to implement

1. `stable_softmax` — max subtraction.
2. `logsumexp` — the shifted identity.
3. `log_softmax` — `x - logsumexp(x)`, never materializing a small probability.
4. `online_softmax_denominator` — the single-pass running max and denominator.
5. `online_weighted_sum` — the FlashAttention accumulator: a softmax-weighted sum computed while streaming, without ever forming the probability vector.

## What the script does differently

It does not assert that stability is good. It **measures the failure**:

- Naive softmax is run at logit scales 1, 10, 50, 90, 200, and the script prints the exact scale at which it stops producing finite numbers.
- `log(softmax(x))` is compared against `x - logsumexp(x)` on the same input; the naive version produces `-inf` entries and an infinite error, and you see it.
- The online recurrence is fed a monotonically increasing stream, where the maximum changes at *every* step and the rescaling factor is doing real work on every iteration.
- A sequential sum is run with an explicit bf16 accumulator against an fp32 one, with float64 as ground truth. The bf16 accumulator comes back ~70% low — and summing 8192 ones in bf16 returns exactly 256, because once the running sum is 256x the increment, adding rounds to nothing. The "compute norms in fp32" rule stops being folklore.

## The one to be able to derive live

$$m_{k+1} = \max(m_k, x_{k+1}), \qquad d_{k+1} = d_k\,e^{m_k - m_{k+1}} + e^{x_{k+1}-m_{k+1}}$$

Then extend it to the weighted sum by rescaling the output accumulator with the same factor. That extension is FlashAttention.
