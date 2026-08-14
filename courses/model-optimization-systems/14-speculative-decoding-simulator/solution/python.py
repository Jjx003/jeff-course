"""
Reference solution for module 14.
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


def acceptance_alpha(p: torch.Tensor, q: torch.Tensor) -> float:
    return float(torch.minimum(p, q).sum())


def residual_distribution(p: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    residual = torch.clamp(p - q, min=0.0)
    return residual / residual.sum()


def emitted_distribution(p: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    """Exact law of the token speculative sampling emits, built from the rule itself."""
    alpha = acceptance_alpha(p, q)
    accept_prob = torch.clamp(p / q, max=1.0)
    return q * accept_prob + (1.0 - alpha) * residual_distribution(p, q)


def emitted_distribution_wrong(p: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    """Same rule, but the rejection replacement is drawn from p instead of p_res."""
    alpha = acceptance_alpha(p, q)
    accept_prob = torch.clamp(p / q, max=1.0)
    return q * accept_prob + (1.0 - alpha) * p


def speculative_sample(p: torch.Tensor, q: torch.Tensor, n: int):
    """Draw n tokens by speculative sampling. Returns (tokens, accepted_mask)."""
    proposal = torch.multinomial(q, n, replacement=True)
    u = torch.rand(n)
    accepted = u < (p[proposal] / q[proposal])
    replacement = torch.multinomial(residual_distribution(p, q), n, replacement=True)
    return torch.where(accepted, proposal, replacement), accepted


def empirical_distribution(tokens: torch.Tensor) -> torch.Tensor:
    return torch.bincount(tokens, minlength=VOCAB).to(torch.float32) / tokens.numel()


def simulate_draft_steps(
    p_table: torch.Tensor,
    q_table: torch.Tensor,
    context_token: int,
    draft_len: int,
    n: int,
):
    """Run n independent speculative steps of length draft_len.

    Returns (accepted_counts, prefix_probs) where prefix_probs[i - 1] is the
    measured probability that the first i drafted tokens all survive.
    """
    context = torch.full((n,), context_token, dtype=torch.long)
    contexts, proposals = [], []
    for _ in range(draft_len):
        contexts.append(context)
        context = torch.multinomial(q_table[context], 1).squeeze(1)
        proposals.append(context)

    alive = torch.ones(n, dtype=torch.bool)
    accepted = torch.zeros(n, dtype=torch.long)
    prefix = []
    for i in range(draft_len):
        index = proposals[i].unsqueeze(1)
        p_x = p_table[contexts[i]].gather(1, index).squeeze(1)
        q_x = q_table[contexts[i]].gather(1, index).squeeze(1)
        alive = alive & (torch.rand(n) < p_x / q_x)
        accepted += alive.long()
        prefix.append(float(alive.to(torch.float32).mean()))
    return accepted, prefix


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
