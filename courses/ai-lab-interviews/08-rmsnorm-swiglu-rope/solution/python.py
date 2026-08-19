"""
RMSNorm, SwiGLU, and RoPE, with the checks that actually distinguish a correct
implementation from a plausible one.

Graded output goes to stdout in float32 with seed 0. Exact floating-point
differences go to stderr, which is not graded.
"""

import sys

import torch
import torch.nn as nn
import torch.nn.functional as F

SEED = 0
BATCH = 2
SEQ = 32
D_MODEL = 64
N_HEADS = 8
HEAD_DIM = D_MODEL // N_HEADS
ROPE_BASE = 10000.0
EPS = 1e-6
TIGHT = 1e-5
NORM_ATOL = 1e-4


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = EPS):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        dtype = x.dtype
        # Reduce in fp32: summing d squared bf16 values loses far too much.
        x32 = x.float()
        normed = x32 * torch.rsqrt(x32.pow(2).mean(-1, keepdim=True) + self.eps)
        return normed.to(dtype) * self.weight


def rmsnorm_reference(x: torch.Tensor, eps: float = EPS) -> torch.Tensor:
    """float64 ground truth, weight fixed at 1."""
    x64 = x.double()
    return x64 / torch.sqrt(x64.pow(2).mean(-1, keepdim=True) + eps)


def naive_bf16_rmsnorm(x: torch.Tensor, eps: float = EPS) -> torch.Tensor:
    """What you get without the upcast: the reduction happens in bf16."""
    return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + eps)


class SwiGLU(nn.Module):
    """Hidden size defaults to 8d/3 so parameters match a 4x ReLU FFN."""

    def __init__(self, dim: int, hidden: int | None = None):
        super().__init__()
        hidden = hidden if hidden is not None else (8 * dim) // 3
        self.hidden = hidden
        self.w_gate = nn.Linear(dim, hidden, bias=False)
        self.w_up = nn.Linear(dim, hidden, bias=False)
        self.w_down = nn.Linear(hidden, dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.w_down(F.silu(self.w_gate(x)) * self.w_up(x))


class ReluFFN(nn.Module):
    """The 4x ReLU MLP SwiGLU replaced, for a parameter-count comparison."""

    def __init__(self, dim: int):
        super().__init__()
        self.up = nn.Linear(dim, 4 * dim, bias=False)
        self.down = nn.Linear(4 * dim, dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down(F.relu(self.up(x)))


def build_rope_cache(seq_len: int, head_dim: int, base: float = ROPE_BASE):
    """Return (cos, sin), each (seq_len, head_dim // 2)."""
    inv_freq = 1.0 / (base ** (torch.arange(0, head_dim, 2).float() / head_dim))
    freqs = torch.outer(torch.arange(seq_len).float(), inv_freq)
    return freqs.cos(), freqs.sin()


def apply_rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor, offset: int = 0) -> torch.Tensor:
    """Rotate (..., S, head_dim) using the interleaved channel convention."""
    seq = x.shape[-2]
    cos_s = cos[offset:offset + seq]
    sin_s = sin[offset:offset + seq]

    x1 = x[..., 0::2]
    x2 = x[..., 1::2]

    rotated = torch.empty_like(x)
    rotated[..., 0::2] = x1 * cos_s - x2 * sin_s
    rotated[..., 1::2] = x1 * sin_s + x2 * cos_s
    return rotated


def rope_score(cos, sin, q: torch.Tensor, k: torch.Tensor, m: int, n: int) -> float:
    """Dot product of q placed at position m with k placed at position n."""
    qm = apply_rope(q.view(1, 1, -1), cos, sin, offset=m).view(-1)
    kn = apply_rope(k.view(1, 1, -1), cos, sin, offset=n).view(-1)
    return float(torch.dot(qm, kn))


def main():
    torch.manual_seed(SEED)
    # Nothing here needs gradients; this keeps the report free of autograd noise.
    torch.set_grad_enabled(False)

    print("=== RMSNorm, SwiGLU, RoPE ===")
    print(f"batch: {BATCH}  seq: {SEQ}  d_model: {D_MODEL}  heads: {N_HEADS}  head_dim: {HEAD_DIM}")

    print()
    print("--- RMSNorm ---")
    norm = RMSNorm(D_MODEL)
    x = torch.randn(BATCH, SEQ, D_MODEL)
    out = norm(x)
    ref = rmsnorm_reference(x)
    print(f"output shape: {tuple(out.shape)}")
    print(f"matches float64 reference: {torch.allclose(out.double(), ref, atol=NORM_ATOL)}")
    print(f"ones input maps to ones: {torch.allclose(norm(torch.ones(1, 1, D_MODEL)), torch.ones(1, 1, D_MODEL), atol=TIGHT)}")
    rms_after = out.float().pow(2).mean(-1).sqrt()
    print(f"row RMS after norm is 1: {torch.allclose(rms_after, torch.ones_like(rms_after), atol=NORM_ATOL)}")
    print(f"  max abs diff vs float64: {float((out.double() - ref).abs().max()):.3e}", file=sys.stderr)

    print()
    print("--- why the fp32 upcast matters ---")
    x_bf16 = (torch.randn(BATCH, SEQ, D_MODEL) * 8.0).bfloat16()
    ref_bf16 = rmsnorm_reference(x_bf16.double())
    norm_bf16 = RMSNorm(D_MODEL).bfloat16()
    with_upcast = norm_bf16(x_bf16).double()
    without_upcast = naive_bf16_rmsnorm(x_bf16).double()
    err_with = float((with_upcast - ref_bf16).abs().max())
    err_without = float((without_upcast - ref_bf16).abs().max())
    print(f"fp32-internal norm is closer to the float64 answer: {err_with < err_without}")
    print(f"error ratio (naive / upcast) exceeds 2x: {err_without > 2 * err_with}")
    print(f"  err with upcast: {err_with:.3e}   err without: {err_without:.3e}", file=sys.stderr)

    print()
    print("--- SwiGLU ---")
    swiglu = SwiGLU(D_MODEL)
    relu_ffn = ReluFFN(D_MODEL)
    swiglu_params = sum(p.numel() for p in swiglu.parameters())
    relu_params = sum(p.numel() for p in relu_ffn.parameters())
    print(f"d_model: {D_MODEL}   swiglu hidden (8d/3): {swiglu.hidden}   relu hidden (4d): {4 * D_MODEL}")
    print(f"swiglu params: {swiglu_params}")
    print(f"relu ffn params: {relu_params}")
    print(f"within 2% of each other: {abs(swiglu_params - relu_params) / relu_params < 0.02}")
    print(f"output shape: {tuple(swiglu(x).shape)}")
    print(f"8d^2 for d={D_MODEL}: {8 * D_MODEL * D_MODEL}")

    print()
    print("--- RoPE is a rotation ---")
    cos, sin = build_rope_cache(SEQ, HEAD_DIM)
    print(f"cache shapes: cos {tuple(cos.shape)}  sin {tuple(sin.shape)}")
    h = torch.randn(BATCH, N_HEADS, SEQ, HEAD_DIM)
    h_rot = apply_rope(h, cos, sin)
    print(f"output shape: {tuple(h_rot.shape)}")
    print(f"norms preserved: {torch.allclose(h.norm(dim=-1), h_rot.norm(dim=-1), atol=TIGHT)}")
    print(f"position 0 is the identity: {torch.allclose(h_rot[:, :, 0], h[:, :, 0], atol=TIGHT)}")

    print()
    print("--- RoPE is relative ---")
    q = torch.randn(HEAD_DIM)
    k = torch.randn(HEAD_DIM)
    print("q at m, k at n; the score should depend only on m - n:")
    relative_ok = True
    for delta in (0, 1, 4):
        scores = [rope_score(cos, sin, q, k, m, m - delta) for m in (delta, delta + 5, delta + 11)]
        spread = max(scores) - min(scores)
        ok = spread < TIGHT
        relative_ok = relative_ok and ok
        print(f"  offset m-n = {delta}: same score at three absolute positions: {ok}")
        print(f"      scores: {[round(s, 6) for s in scores]}", file=sys.stderr)

    print()
    print("--- RoPE is not a no-op ---")
    distinct = [round(rope_score(cos, sin, q, k, 0, n), 4) for n in (0, 1, 2, 8)]
    print(f"scores at offsets 0, -1, -2, -8 are distinct: {len(set(distinct)) == len(distinct)}")
    print(f"  scores: {distinct}", file=sys.stderr)

    print()
    all_ok = (
        torch.allclose(out.double(), ref, atol=NORM_ATOL)
        and err_with < err_without
        and abs(swiglu_params - relu_params) / relu_params < 0.02
        and torch.allclose(h.norm(dim=-1), h_rot.norm(dim=-1), atol=TIGHT)
        and relative_ok
        and len(set(distinct)) == len(distinct)
    )
    print(f"ALL CHECKS PASS: {all_ok}")


if __name__ == "__main__":
    main()
