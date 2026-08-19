"""
Causal multi-head attention and grouped-query attention, checked against
torch's fused kernel.

Graded output goes to stdout in float32 with seed 0 so the numbers match on
any machine. Exact floating-point differences go to stderr, which is not
graded, because they depend on the BLAS reduction order of your CPU.

Fill in the five TODO blocks. Autocomplete off, timer on: fifteen minutes for
`attention` and `MultiHeadAttention.forward` is the interview bar.
"""

import math
import sys

import torch
import torch.nn as nn
import torch.nn.functional as F

SEED = 0
BATCH = 2
SEQ = 16
D_MODEL = 64
N_HEADS = 8
N_KV_HEADS = 2
HEAD_DIM = D_MODEL // N_HEADS
FUSED_ATOL = 1e-5
EXACT_ATOL = 1e-6

# Realistic serving config, used only for the KV-cache arithmetic report.
REPORT_LAYERS = 32
REPORT_HEAD_DIM = 128
REPORT_SEQ = 4096
REPORT_BYTES = 2
GB = 1000 ** 3


def split_heads(x: torch.Tensor, n_heads: int) -> torch.Tensor:
    """(B, S, n_heads * head_dim) -> (B, n_heads, S, head_dim).

    TODO 1: view the last axis apart into (n_heads, head_dim), then transpose
    heads in front of sequence.

    Order matters. `view(B, S, n_heads, head_dim)` splits the feature axis,
    which is where the heads actually live. `view(B, n_heads, S, head_dim)`
    would slice along the sequence axis and mix tokens into heads — same
    shape, silently wrong.
    """
    raise NotImplementedError


def merge_heads(x: torch.Tensor) -> torch.Tensor:
    """(B, H, S, head_dim) -> (B, S, H * head_dim).

    TODO 2: transpose back, then flatten the last two axes.

    You will need `.contiguous()` between them: transpose only permutes
    strides, and `view` requires contiguous memory.
    """
    raise NotImplementedError


def causal_mask(seq: int, device=None) -> torch.Tensor:
    """(S, S) boolean, True where attention is allowed.

    TODO 3: lower triangle including the diagonal — query i may attend to
    keys 0..i, itself included.
    """
    raise NotImplementedError


def repeat_kv(x: torch.Tensor, n_rep: int) -> torch.Tensor:
    """(B, G, S, head_dim) -> (B, G * n_rep, S, head_dim), groups contiguous.

    TODO 4: expand each KV head to serve n_rep query heads.

    `repeat_interleave`, not `repeat`. With H=8 and G=2, interleave gives head
    order [0,0,0,0,1,1,1,1]; repeat gives [0,1,0,1,0,1,0,1]. Both have the
    right shape; only the first matches how the weights were grouped.
    """
    raise NotImplementedError


def attention(q: torch.Tensor, k: torch.Tensor, v: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """Explicit scaled dot-product attention. All inputs (B, H, S, head_dim).

    TODO 5a:
      scores = q @ k.transpose(-2, -1) / sqrt(head_dim)     (B, H, S, S)
      scores = scores.masked_fill(~mask, -inf)              before the softmax
      probs  = scores.softmax(dim=-1)
      return probs @ v                                      (B, H, S, head_dim)

    Mask before the softmax, not after: zeroing probabilities afterwards
    leaves the rows unnormalized.
    """
    raise NotImplementedError


class MultiHeadAttention(nn.Module):
    """Causal self-attention. n_kv_heads < n_heads turns this into GQA."""

    def __init__(self, d_model: int, n_heads: int, n_kv_heads: int | None = None):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads if n_kv_heads is not None else n_heads
        self.head_dim = d_model // n_heads
        self.n_rep = self.n_heads // self.n_kv_heads

        self.wq = nn.Linear(d_model, n_heads * self.head_dim, bias=False)
        self.wk = nn.Linear(d_model, self.n_kv_heads * self.head_dim, bias=False)
        self.wv = nn.Linear(d_model, self.n_kv_heads * self.head_dim, bias=False)
        self.wo = nn.Linear(n_heads * self.head_dim, d_model, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """TODO 5b: project, split heads, repeat KV, attend, merge, project out.

        Note that q splits into self.n_heads while k and v split into
        self.n_kv_heads — that asymmetry is the whole of GQA.
        """
        raise NotImplementedError


def _ref_split(x: torch.Tensor, n_heads: int) -> torch.Tensor:
    """Head split, written out in the harness so it cannot share a bug with
    your split_heads."""
    b, s, _ = x.shape
    return x.view(b, s, n_heads, x.shape[-1] // n_heads).transpose(1, 2)


def _ref_expand_kv(x: torch.Tensor, n_rep: int) -> torch.Tensor:
    """Expand G KV heads to G * n_rep, groups contiguous.

    Deliberately does NOT call your repeat_kv. If the oracle used your
    expansion, a repeat/repeat_interleave mix-up would cancel out on both
    sides and the GQA check could never fail.
    """
    if n_rep == 1:
        return x
    b, g, s, head_dim = x.shape
    return x[:, :, None, :, :].expand(b, g, n_rep, s, head_dim).reshape(b, g * n_rep, s, head_dim)


def fused_reference(module: MultiHeadAttention, x: torch.Tensor) -> torch.Tensor:
    """Same weights, but every step comes from the harness, not from you."""
    b, seq, d = x.shape
    q = _ref_split(module.wq(x), module.n_heads)
    k = _ref_expand_kv(_ref_split(module.wk(x), module.n_kv_heads), module.n_rep)
    v = _ref_expand_kv(_ref_split(module.wv(x), module.n_kv_heads), module.n_rep)
    out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
    return module.wo(out.transpose(1, 2).contiguous().view(b, seq, d))


def causality_violation(module: MultiHeadAttention, x: torch.Tensor, t: int) -> float:
    """Max change at positions < t when the input at position t is replaced."""
    with torch.no_grad():
        base = module(x)
        perturbed_input = x.clone()
        perturbed_input[:, t, :] = torch.randn_like(perturbed_input[:, t, :]) * 10.0
        perturbed = module(perturbed_input)
    return float((base[:, :t, :] - perturbed[:, :t, :]).abs().max())


def kv_cache_gb(n_kv_heads: int) -> float:
    per_token_per_layer = 2 * n_kv_heads * REPORT_HEAD_DIM * REPORT_BYTES
    return per_token_per_layer * REPORT_SEQ * REPORT_LAYERS / GB


def main():
    torch.manual_seed(SEED)
    torch.set_printoptions(precision=6)

    x = torch.randn(BATCH, SEQ, D_MODEL)

    print("=== Causal multi-head attention ===")
    print(f"batch: {BATCH}  seq: {SEQ}  d_model: {D_MODEL}  heads: {N_HEADS}  head_dim: {HEAD_DIM}")
    print(f"softmax scale (1/sqrt(head_dim)): {1.0 / math.sqrt(HEAD_DIM):.5f}")

    print()
    print("--- shapes ---")
    q = split_heads(torch.randn(BATCH, SEQ, D_MODEL), N_HEADS)
    print(f"after split_heads: {tuple(q.shape)}")
    print(f"after merge_heads: {tuple(merge_heads(q).shape)}")
    mask = causal_mask(SEQ)
    print(f"causal mask: {tuple(mask.shape)}  allowed entries: {int(mask.sum())}")
    print(f"expected allowed entries S(S+1)/2: {SEQ * (SEQ + 1) // 2}")

    print()
    print("--- MHA vs torch fused kernel ---")
    mha = MultiHeadAttention(D_MODEL, N_HEADS)
    with torch.no_grad():
        mine = mha(x)
        theirs = fused_reference(mha, x)
    print(f"output shape: {tuple(mine.shape)}")
    print(f"matches fused kernel: {torch.allclose(mine, theirs, atol=FUSED_ATOL)}")
    print(f"  max abs diff: {float((mine - theirs).abs().max()):.3e}", file=sys.stderr)

    print()
    print("--- causality, tested behaviorally ---")
    violations = [causality_violation(mha, x, t) for t in (1, SEQ // 2, SEQ - 1)]
    for t, delta in zip((1, SEQ // 2, SEQ - 1), violations):
        print(f"  perturb position {t:>2}: earlier outputs unchanged: {delta < EXACT_ATOL}")
        print(f"      max delta: {delta:.3e}", file=sys.stderr)
    print(f"no information flows backward: {all(d < EXACT_ATOL for d in violations)}")

    print()
    print("--- grouped-query attention ---")
    gqa = MultiHeadAttention(D_MODEL, N_HEADS, n_kv_heads=N_KV_HEADS)
    with torch.no_grad():
        gqa_mine = gqa(x)
        gqa_fused = fused_reference(gqa, x)
    print(f"query heads: {N_HEADS}  kv heads: {N_KV_HEADS}  repeats per group: {N_HEADS // N_KV_HEADS}")
    print(f"output shape: {tuple(gqa_mine.shape)}")
    print(f"matches fused kernel: {torch.allclose(gqa_mine, gqa_fused, atol=FUSED_ATOL)}")
    print(f"  max abs diff: {float((gqa_mine - gqa_fused).abs().max()):.3e}", file=sys.stderr)

    degenerate = MultiHeadAttention(D_MODEL, N_HEADS, n_kv_heads=N_HEADS)
    degenerate.load_state_dict(mha.state_dict())
    with torch.no_grad():
        degenerate_ok = torch.allclose(degenerate(x), mine, atol=EXACT_ATOL)
    print(f"GQA with G == H reproduces MHA: {degenerate_ok}")

    # repeat_interleave and repeat produce the same shape and a different
    # grouping. This is the check that separates them.
    with torch.no_grad():
        grouped = repeat_kv(torch.arange(N_KV_HEADS, dtype=torch.float32).view(1, N_KV_HEADS, 1, 1), N_HEADS // N_KV_HEADS)
    head_order = [int(v) for v in grouped.flatten()]
    expected_order = [h for h in range(N_KV_HEADS) for _ in range(N_HEADS // N_KV_HEADS)]
    print(f"KV head order after expansion: {head_order}")
    print(f"groups are contiguous (repeat_interleave, not repeat): {head_order == expected_order}")

    kv_params_mha = 2 * D_MODEL * N_HEADS * HEAD_DIM
    kv_params_gqa = 2 * D_MODEL * N_KV_HEADS * HEAD_DIM
    print(f"K+V projection params, MHA: {kv_params_mha}")
    print(f"K+V projection params, GQA: {kv_params_gqa}")
    print(f"reduction factor: {kv_params_mha // kv_params_gqa}x")

    print()
    print("--- what the KV cache costs in production ---")
    print(f"config: {REPORT_LAYERS} layers, head_dim {REPORT_HEAD_DIM}, {REPORT_SEQ} tokens, bf16")
    for label, kv_heads in (("MHA (32 kv heads)", 32), ("GQA (8 kv heads)", 8), ("MQA (1 kv head)", 1)):
        print(f"  {label:<20} {kv_cache_gb(kv_heads):.2f} GB per sequence")

    print()
    all_ok = (
        torch.allclose(mine, theirs, atol=FUSED_ATOL)
        and all(d < EXACT_ATOL for d in violations)
        and torch.allclose(gqa_mine, gqa_fused, atol=FUSED_ATOL)
        and degenerate_ok
        and head_order == expected_order
    )
    print(f"ALL CHECKS PASS: {all_ok}")


if __name__ == "__main__":
    main()
