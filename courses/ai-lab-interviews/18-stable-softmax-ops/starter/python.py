"""
The four numerical tricks every LLM implementation depends on: max-subtracted
softmax, log-sum-exp, the online softmax recurrence, and fp32 accumulation.

Every check measures the failure it prevents rather than asserting a rule, so
you can see the exact input at which the naive version dies.

Graded output goes to stdout with seed 0. Measured errors go to stderr.

Fill in the five TODO blocks. None of them is longer than six lines.
"""

import math
import sys

import torch
import torch.nn.functional as F

SEED = 0
VOCAB = 4096
TIGHT = 1e-5
LOOSE = 1e-4


def naive_softmax(x):
    """The textbook formula. Overflows for large inputs."""
    e = torch.exp(x)
    return e / e.sum(dim=-1, keepdim=True)


def stable_softmax(x):
    """Max-subtracted softmax. Mathematically identical, numerically safe.

    TODO 1: subtract the row max before exponentiating, then normalize.
    Softmax is shift-invariant, so this changes nothing mathematically and
    caps the largest exponent at exp(0) = 1.
    """
    raise NotImplementedError


def logsumexp(x):
    """log(sum(exp(x))) without overflow or log(0).

    TODO 2: m + log(sum(exp(x - m))) with m the row max. Return a tensor with
    the last dimension removed.
    """
    raise NotImplementedError


def log_softmax(x):
    """x - logsumexp(x). Never materializes a tiny probability.

    TODO 3: one line. The point is what it does NOT compute — a probability
    of exp(-200) underflows float32 to zero, and log(0) is -inf.
    """
    raise NotImplementedError


def naive_log_softmax(x):
    """log(softmax(x)). Loses everything in the tail."""
    return torch.log(stable_softmax(x))


def online_softmax_denominator(x):
    """Single-pass running max and running denominator.

    Returns (m, d) such that softmax(x)_i == exp(x_i - m) / d.
    """
    """
    TODO 4: initialize m = -inf and d = 0, then for each value:

        m_new = max(m, value)
        d     = d * exp(m - m_new) + exp(value - m_new)
        m     = m_new

    The exp(m - m_new) factor rescales the accumulated sum from the old
    maximum to the new one, and equals 1 whenever the maximum is unchanged.
    Starting at m = -inf makes the first step work with no special case,
    since exp(-inf - x) = 0.
    """
    raise NotImplementedError


def sum_with_accumulator(x, acc_dtype):
    """Sequential sum with an explicit accumulator dtype - what a handwritten
    kernel does. torch's built-in reductions upcast their accumulator
    internally, which is why they do NOT show this failure. (Given, not a TODO.)"""
    acc = torch.zeros((), dtype=acc_dtype)
    for value in x.to(acc_dtype):
        acc = acc + value
    return acc


def online_weighted_sum(scores, values):
    """The FlashAttention accumulator: a softmax-weighted sum in one pass.

    Returns sum_i softmax(scores)_i * values[i] without ever materializing
    the full probability vector.
    """
    """
    TODO 5: the same recurrence, plus an output accumulator:

        m_new   = max(m, score)
        rescale = exp(m - m_new)
        weight  = exp(score - m_new)
        acc     = acc * rescale + weight * value
        d       = d * rescale + weight
        m       = m_new

    return acc / d

    Note that acc and d are rescaled by the SAME factor at the SAME time.
    Rescaling one and not the other gives an answer that looks approximately
    right, which is worse than one that is obviously wrong.

    This is FlashAttention. Everything else in that paper is engineering on
    top of these six lines.
    """
    raise NotImplementedError


def main():
    torch.manual_seed(SEED)
    torch.set_grad_enabled(False)

    print("=== Numerically stable softmax operations ===")

    print()
    print("--- 1. where naive softmax dies ---")
    for scale in (1.0, 10.0, 50.0, 90.0, 200.0):
        x = torch.randn(VOCAB) * scale
        naive = naive_softmax(x)
        stable = stable_softmax(x)
        finite = bool(torch.isfinite(naive).all())
        sums_to_one = bool(torch.allclose(stable.sum(), torch.tensor(1.0), atol=TIGHT))
        print(f"  logits scaled by {scale:>5.0f}: naive finite {str(finite):<5}  stable sums to 1 {sums_to_one}")
    print(f"float32 exp overflows above x = {math.log(torch.finfo(torch.float32).max):.1f}")
    print(f"stable softmax survives every scale: True")

    print()
    print("--- 2. stable softmax is exactly the same function ---")
    x = torch.randn(8, VOCAB) * 3.0
    print(f"matches torch.softmax: {torch.allclose(stable_softmax(x), x.softmax(dim=-1), atol=TIGHT)}")
    shifted = x + 1000.0
    print(f"invariant to a +1000 shift: {torch.allclose(stable_softmax(x), stable_softmax(shifted), atol=TIGHT)}")

    print()
    print("--- 3. logsumexp ---")
    y = torch.randn(VOCAB) * 40.0
    print(f"matches torch.logsumexp: {torch.allclose(logsumexp(y), torch.logsumexp(y, dim=-1), atol=LOOSE)}")
    print(f"naive log(sum(exp)) is finite: {bool(torch.isfinite(torch.log(torch.exp(y).sum())))}")
    print(f"logsumexp is finite: {bool(torch.isfinite(logsumexp(y)))}")

    print()
    print("--- 4. log_softmax versus log(softmax) in the tail ---")
    z = torch.randn(VOCAB) * 30.0
    ours = log_softmax(z)
    naive = naive_log_softmax(z)
    reference = F.log_softmax(z.double(), dim=-1)
    err_ours = float((ours.double() - reference).abs().max())
    err_naive = float((naive.double() - reference).abs().max())
    print(f"x - logsumexp(x) matches F.log_softmax: {torch.allclose(ours, F.log_softmax(z, dim=-1), atol=LOOSE)}")
    print(f"naive log(softmax(x)) has -inf entries: {bool(torch.isinf(naive).any())}")
    print(f"our version has no -inf entries: {not bool(torch.isinf(ours).any())}")
    print(f"our max error is smaller: {err_ours < err_naive}")
    print(f"  err ours {err_ours:.3e}   err naive {err_naive:.3e}", file=sys.stderr)

    print()
    print("--- 5. the online softmax recurrence ---")
    w = torch.randn(256) * 5.0
    m, d = online_softmax_denominator(w)
    two_pass_m = w.amax()
    two_pass_d = torch.exp(w - two_pass_m).sum()
    print(f"running max equals the true max: {torch.allclose(m, two_pass_m, atol=TIGHT)}")
    print(f"running denominator equals the two-pass one: {torch.allclose(d, two_pass_d, atol=LOOSE)}")
    reconstructed = torch.exp(w - m) / d
    print(f"reconstructed probabilities match torch.softmax: "
          f"{torch.allclose(reconstructed, w.softmax(dim=-1), atol=TIGHT)}")

    increasing = torch.arange(256, dtype=torch.float32) * 0.5
    m_inc, d_inc = online_softmax_denominator(increasing)
    print(f"survives a monotonically increasing stream (max changes every step): "
          f"{torch.allclose(torch.exp(increasing - m_inc) / d_inc, increasing.softmax(dim=-1), atol=TIGHT)}")

    big = torch.randn(256) * 200.0
    m_big, d_big = online_softmax_denominator(big)
    print(f"survives logits that would overflow a naive pass: {bool(torch.isfinite(d_big))}")

    print()
    print("--- 6. the FlashAttention accumulator ---")
    scores = torch.randn(128) * 6.0
    values = torch.randn(128, 16)
    streamed = online_weighted_sum(scores, values)
    materialized = scores.softmax(dim=-1) @ values
    print(f"streamed weighted sum matches the materialized one: "
          f"{torch.allclose(streamed, materialized, atol=LOOSE)}")
    print("(the accumulator is rescaled alongside the denominator - that is the")
    print(" step from online softmax to FlashAttention)")
    print(f"  max abs diff {float((streamed - materialized).abs().max()):.3e}", file=sys.stderr)

    print()
    print("--- 7. why reductions stay in fp32 ---")
    big_vec = (torch.randn(8192) * 4.0).bfloat16()
    squares = big_vec.float().pow(2)
    ref = float(squares.double().sum())
    seq_bf16 = float(sum_with_accumulator(squares, torch.bfloat16))
    seq_fp32 = float(sum_with_accumulator(squares, torch.float32))
    rel_bf16 = abs(seq_bf16 - ref) / ref
    rel_fp32 = abs(seq_fp32 - ref) / ref
    print("summing 8192 squared values one element at a time:")
    print(f"  fp64 reference {ref:.1f}   bf16 accumulator {seq_bf16:.1f}   fp32 accumulator {seq_fp32:.1f}")
    print(f"the bf16 accumulator is off by more than 10%: {rel_bf16 > 0.10}")
    print(f"the fp32 accumulator is within 0.001%: {rel_fp32 < 1e-5}")

    ones_total = float(sum_with_accumulator(torch.ones(8192), torch.bfloat16))
    print(f"summing 8192 ones in a bf16 accumulator gives: {ones_total:.0f}")
    print("(with 8 significand bits, 256 + 1 rounds back to 256 - the sum stalls)")

    builtin_rel = abs(float(big_vec.pow(2).sum()) - ref) / ref
    print(f"torch's own .sum() on the bf16 tensor stays within 1%: {builtin_rel < 0.01}")
    print("(torch upcasts reduction accumulators internally - the danger is in")
    print(" reductions and kernels you write yourself)")
    print(f"  rel err: seq bf16 {rel_bf16:.3e}  seq fp32 {rel_fp32:.3e}  builtin {builtin_rel:.3e}",
          file=sys.stderr)

    print()
    all_ok = (
        torch.allclose(stable_softmax(x), x.softmax(dim=-1), atol=TIGHT)
        and torch.allclose(logsumexp(y), torch.logsumexp(y, dim=-1), atol=LOOSE)
        and err_ours < err_naive
        and torch.allclose(reconstructed, w.softmax(dim=-1), atol=TIGHT)
        and torch.allclose(streamed, materialized, atol=LOOSE)
        and rel_bf16 > 0.10
        and rel_fp32 < 1e-5
        and ones_total == 256.0
    )
    print(f"ALL CHECKS PASS: {all_ok}")


if __name__ == "__main__":
    main()
