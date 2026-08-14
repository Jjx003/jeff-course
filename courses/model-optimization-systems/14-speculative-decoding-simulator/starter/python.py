"""
Speculative sampling: implement the accept/reject rule and prove it is lossless.

The target and draft are real (tiny) torch modules. Everything runs on CPU in
float32 with a fixed seed, so the Monte Carlo numbers you print are exactly the
ones the grader expects. Wall-clock timing goes to stderr and is not graded.

See problem.md for the required output format.
"""

import math
import sys
import time

import torch

VOCAB = 64
TARGET_HIDDEN = 64
TARGET_TEMP = 0.30
CONTEXT_TOKEN = 7
TRIALS = 200_000
STEP_TRIALS = 100_000
MAX_DRAFT = 8
DRAFT_LENGTHS = [2, 4, 8]
TV_TOL = 0.02
DRAFT_CONFIGS = [
    ("strong draft", 48, 0.20),
    ("weak draft", 2, 0.60),
]


class TinyLM(torch.nn.Module):
    """A bigram language model: next-token logits depend only on the last token."""

    def __init__(self, vocab: int, hidden: int) -> None:
        super().__init__()
        self.embed = torch.nn.Embedding(vocab, hidden)
        self.head = torch.nn.Linear(hidden, vocab)

    def forward(self, context: torch.Tensor) -> torch.Tensor:
        return self.head(self.embed(context))


def width_pruned_draft(target: TinyLM, hidden: int) -> TinyLM:
    """Build a draft by keeping only the first `hidden` channels of the target."""
    draft = TinyLM(VOCAB, hidden)
    with torch.no_grad():
        draft.embed.weight.copy_(target.embed.weight[:, :hidden])
        draft.head.weight.copy_(target.head.weight[:, :hidden])
        draft.head.bias.copy_(target.head.bias)
    return draft


@torch.inference_mode()
def distribution_table(model: TinyLM, temperature: float) -> torch.Tensor:
    """Return a (VOCAB, VOCAB) table: row c is the next-token distribution after c."""
    return torch.softmax(model(torch.arange(VOCAB)) / temperature, dim=-1)


def total_variation(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(0.5 * (a - b).abs().sum())


def entropy(p: torch.Tensor) -> float:
    return float(-(p * p.clamp_min(1e-30).log()).sum())


def empirical_distribution(tokens: torch.Tensor) -> torch.Tensor:
    return torch.bincount(tokens, minlength=VOCAB).to(torch.float32) / tokens.numel()


def acceptance_alpha(p: torch.Tensor, q: torch.Tensor) -> float:
    """Return alpha = sum_t min(p_t, q_t), the probability a proposal is accepted."""
    # TODO 1: One line. torch.minimum, then sum, then float(). This is also
    # 1 - TV(p, q), which the program checks for you.
    raise NotImplementedError


def residual_distribution(p: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    """Return p_res(t) proportional to max(0, p(t) - q(t)), normalized to sum to 1.

    This is where the target puts the mass the draft could not cover. Sampling
    the replacement from p instead of p_res is the classic bug.
    """
    # TODO 2: Clamp p - q at 0, then divide by its own sum. The sum is exactly
    # 1 - alpha, which is why it is never zero unless q == p.
    raise NotImplementedError


def emitted_distribution(p: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    """Exact law of the token speculative sampling emits, built from the rule itself.

    emitted(t) = q(t) * min(1, p(t)/q(t)) + (1 - alpha) * p_res(t)

    The first term is "the draft proposed t and it survived". The second is
    "something was rejected and the residual draw happened to land on t".
    """
    # TODO 3: Build accept_prob = min(1, p/q) with torch.clamp(..., max=1.0),
    # then return q * accept_prob + (1 - alpha) * p_res. Do not shortcut this
    # to torch.minimum(p, q) + ...; write the rule as stated so the check is
    # testing the rule and not an algebraic rewrite of the answer.
    raise NotImplementedError


def emitted_distribution_wrong(p: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    """Same rule, but the rejection replacement is drawn from p instead of p_res."""
    # TODO 4: Identical to TODO 3 with p substituted for the residual. This
    # still sums to 1, which is exactly why the bug survives casual testing.
    raise NotImplementedError


def speculative_sample(p: torch.Tensor, q: torch.Tensor, n: int):
    """Draw n tokens by speculative sampling. Returns (tokens, accepted_mask)."""
    # TODO 5: Vectorize over all n trials; do not write a Python loop.
    #   proposal    = torch.multinomial(q, n, replacement=True)      -> (n,)
    #   u           = torch.rand(n)
    #   accepted    = u < p[proposal] / q[proposal]
    #     (min(1, .) is redundant here because u < 1 always, but say why.)
    #   replacement = torch.multinomial(residual_distribution(p, q), n,
    #                                   replacement=True)
    # Return torch.where(accepted, proposal, replacement) and accepted.
    # Drawing every replacement up front and selecting with torch.where is fine:
    # the replacements are independent of the accept decisions.
    raise NotImplementedError


def simulate_draft_steps(
    p_table: torch.Tensor,
    q_table: torch.Tensor,
    context_token: int,
    draft_len: int,
    n: int,
):
    """Run n independent speculative steps of length draft_len.

    Returns (accepted_counts, prefix_probs) where accepted_counts is an (n,)
    long tensor of accepted draft tokens per step, and prefix_probs[i - 1] is
    the measured probability that the first i drafted tokens all survive.
    """
    # TODO 6a: Drafting phase. Starting from `context_token` for all n lanes,
    # autoregressively sample draft_len tokens from q_table. Keep two lists:
    #   contexts[i]  -> the (n,) context that position i was drafted from
    #   proposals[i] -> the (n,) drafted token at position i
    # The draft always produces all draft_len tokens; verification is what
    # truncates. Use torch.multinomial(q_table[context], 1).squeeze(1).
    #
    # TODO 6b: Verification phase. The target scores every position from the
    # drafted contexts in parallel, then you walk the positions in order:
    #   p_x, q_x = the probabilities of proposals[i] under p_table[contexts[i]]
    #              and q_table[contexts[i]]  (use .gather(1, idx).squeeze(1))
    #   alive    = alive & (torch.rand(n) < p_x / q_x)
    # `alive` must only ever go from True to False: one rejection kills the
    # rest of the draft. Accumulate accepted += alive.long() and append
    # float(alive.to(torch.float32).mean()) to the prefix list.
    raise NotImplementedError


def main() -> None:
    torch.manual_seed(0)
    started = time.perf_counter()

    target = TinyLM(VOCAB, TARGET_HIDDEN)
    p_table = distribution_table(target, TARGET_TEMP)
    p = p_table[CONTEXT_TOKEN]

    print("=== Speculative sampling from a tiny target/draft pair ===")
    print(f"vocab: {VOCAB}")
    print(f"target hidden dim: {TARGET_HIDDEN}")
    print(f"p table shape: {tuple(p_table.shape)}")
    print(f"p table dtype: {p_table.dtype}")
    print(f"context token: {CONTEXT_TOKEN}")
    print(f"p entropy: {entropy(p):.4f} nats (uniform = {math.log(VOCAB):.4f})")
    print(f"p top-1: {float(p.max()):.4f}")
    print()

    for label, hidden, temperature in DRAFT_CONFIGS:
        draft_model = width_pruned_draft(target, hidden)
        q_table = distribution_table(draft_model, temperature)
        q = q_table[CONTEXT_TOKEN]

        alpha = acceptance_alpha(p, q)
        tv_pq = total_variation(p, q)
        alpha_all = torch.minimum(p_table, q_table).sum(dim=-1)

        print(f"=== {label} (hidden {hidden}, temperature {temperature:.2f}) ===")
        print(f"draft parameters: {sum(t.numel() for t in draft_model.parameters())}")
        print(f"q entropy: {entropy(q):.4f} nats")
        print(f"TV(p, q): {tv_pq:.4f}")
        print(f"alpha: {alpha:.4f}")
        print(f"alpha == 1 - TV(p, q): {abs(alpha - (1.0 - tv_pq)) < 1e-5}")
        print(
            f"alpha across all {VOCAB} contexts: "
            f"min={float(alpha_all.min()):.4f} "
            f"mean={float(alpha_all.mean()):.4f} "
            f"max={float(alpha_all.max()):.4f}"
        )
        print()

        emitted = emitted_distribution(p, q)
        max_dev = float((emitted - p).abs().max())
        wrong = emitted_distribution_wrong(p, q)

        print("--- exact identity: q*min(1, p/q) + (1 - alpha)*p_res == p ---")
        print(f"max |emitted - p|: {max_dev:.6f}")
        print(f"allclose(emitted, p): {torch.allclose(emitted, p, atol=1e-6)}")
        print(f"emitted sums to 1: {abs(float(emitted.sum()) - 1.0) < 1e-5}")
        print(f"replacement drawn from p instead: TV(wrong, p) = {total_variation(wrong, p):.4f}")
        print()
        print(f"[measured] {label}: max|emitted - p| = {max_dev:.3e}", file=sys.stderr)

        spec_tokens, accepted = speculative_sample(p, q, TRIALS)
        direct_tokens = torch.multinomial(p, TRIALS, replacement=True)
        spec_empirical = empirical_distribution(spec_tokens)
        direct_empirical = empirical_distribution(direct_tokens)
        tv_spec_direct = total_variation(spec_empirical, direct_empirical)
        tv_spec_exact = total_variation(spec_empirical, p)

        print(f"--- Monte Carlo, {TRIALS} trials ---")
        print(f"empirical acceptance: {float(accepted.to(torch.float32).mean()):.4f} (alpha {alpha:.4f})")
        print(f"TV(speculative, direct p samples): {tv_spec_direct:.4f}")
        print(f"TV(speculative, p exact): {tv_spec_exact:.4f}")
        print(f"TV(q, p) for contrast: {tv_pq:.4f}")
        print(f"lossless within {TV_TOL:.2f}: {tv_spec_direct < TV_TOL and tv_spec_exact < TV_TOL}")
        print()

        counts, prefix = simulate_draft_steps(p_table, q_table, CONTEXT_TOKEN, MAX_DRAFT, STEP_TRIALS)

        print(f"--- prefix survival over {STEP_TRIALS} speculative steps ---")
        for i, measured in enumerate(prefix, start=1):
            print(f"  i={i} measured={measured:.4f} alpha^i={alpha ** i:.4f}")
        print()

        print("--- committed tokens per verification step ---")
        for k in DRAFT_LENGTHS:
            committed = float(counts.clamp(max=k).to(torch.float32).mean()) + 1.0
            predicted = 1.0 + sum(alpha ** i for i in range(1, k + 1))
            print(
                f"  k={k} measured={committed:.4f} predicted={predicted:.4f} "
                f"rel_err={(committed - predicted) / predicted:+.4f}"
            )
        print()

    print(f"[measured] total wall clock: {time.perf_counter() - started:.2f} s", file=sys.stderr)


if __name__ == "__main__":
    main()
