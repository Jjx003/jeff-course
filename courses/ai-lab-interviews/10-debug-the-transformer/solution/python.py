"""
Debug the transformer.

The MODEL section below is what you fix. The HARNESS section below it is a set
of independent reference implementations and probes; do not edit it — it is
what tells you which component is wrong.

The probes run from most local to most global. Fix the first failing one, rerun,
repeat. That ordering is the whole method: a failure at the bottom of the list
tells you almost nothing until everything above it passes.

Graded output goes to stdout with seed 0. Diagnostics go to stderr.
"""

import math
import sys

import torch
import torch.nn as nn
import torch.nn.functional as F

SEED = 0
VOCAB = 512
D_MODEL = 64
N_LAYERS = 4
N_HEADS = 8
HEAD_DIM = D_MODEL // N_HEADS
MAX_SEQ = 64
ROPE_BASE = 10000.0
EPS = 1e-6
INIT_STD = 0.02

BATCH = 2
SEQ = 24
TRAIN_STEPS = 300
LEARNING_RATE = 3e-3
MEMORIZE_LEN = 20
INIT_LOSS_TOL = 0.3
FUSED_ATOL = 1e-5
EXACT_ATOL = 1e-6
RMS_TOL = 0.05


# ==========================================================================
# MODEL — this is the part with bugs in it.
# ==========================================================================


def causal_mask(seq, device=None):
    """(S, S) boolean, True where attention is allowed."""
    return torch.ones(seq, seq, dtype=torch.bool, device=device).tril()


def split_heads(x, n_heads):
    """(B, S, n_heads * head_dim) -> (B, n_heads, S, head_dim)."""
    b, s, _ = x.shape
    head_dim = x.shape[-1] // n_heads
    return x.view(b, s, n_heads, head_dim).transpose(1, 2)


def merge_heads(x):
    """(B, H, S, head_dim) -> (B, S, H * head_dim)."""
    b, h, s, head_dim = x.shape
    return x.transpose(1, 2).contiguous().view(b, s, h * head_dim)


def attention(q, k, v, mask):
    """Scaled dot-product attention over (B, H, S, head_dim) tensors."""
    head_dim = q.shape[-1]
    scores = q @ k.transpose(-2, -1) / math.sqrt(head_dim)
    scores = scores.masked_fill(~mask, float("-inf"))
    return scores.softmax(dim=-1) @ v


def build_rope_cache(seq_len, head_dim, base=ROPE_BASE):
    inv_freq = 1.0 / (base ** (torch.arange(0, head_dim, 2).float() / head_dim))
    freqs = torch.outer(torch.arange(seq_len).float(), inv_freq)
    return freqs.cos(), freqs.sin()


def apply_rope(x, cos, sin):
    seq = x.shape[-2]
    cos_s, sin_s = cos[:seq], sin[:seq]
    x1, x2 = x[..., 0::2], x[..., 1::2]
    out = torch.empty_like(x)
    out[..., 0::2] = x1 * cos_s - x2 * sin_s
    out[..., 1::2] = x1 * sin_s + x2 * cos_s
    return out


class RMSNorm(nn.Module):
    def __init__(self, dim, eps=EPS):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        dtype = x.dtype
        x32 = x.float()
        normed = x32 * torch.rsqrt(x32.pow(2).mean(-1, keepdim=True) + self.eps)
        return normed.to(dtype) * self.weight


class Attention(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.wq = nn.Linear(d_model, d_model, bias=False)
        self.wk = nn.Linear(d_model, d_model, bias=False)
        self.wv = nn.Linear(d_model, d_model, bias=False)
        self.wo = nn.Linear(d_model, d_model, bias=False)

    def forward(self, x, cos, sin):
        s = x.shape[1]
        q = split_heads(self.wq(x), self.n_heads)
        k = split_heads(self.wk(x), self.n_heads)
        v = split_heads(self.wv(x), self.n_heads)

        q = apply_rope(q, cos, sin)
        k = apply_rope(k, cos, sin)

        out = attention(q, k, v, causal_mask(s, x.device))
        return self.wo(merge_heads(out))


class SwiGLU(nn.Module):
    def __init__(self, dim):
        super().__init__()
        hidden = (8 * dim) // 3
        self.w_gate = nn.Linear(dim, hidden, bias=False)
        self.w_up = nn.Linear(dim, hidden, bias=False)
        self.w_down = nn.Linear(hidden, dim, bias=False)

    def forward(self, x):
        return self.w_down(F.silu(self.w_gate(x)) * self.w_up(x))


class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        self.norm1 = RMSNorm(d_model)
        self.attn = Attention(d_model, n_heads)
        self.norm2 = RMSNorm(d_model)
        self.ffn = SwiGLU(d_model)

    def forward(self, x, cos, sin):
        x = x + self.attn(self.norm1(x), cos, sin)
        x = x + self.ffn(self.norm2(x))
        return x


class TransformerLM(nn.Module):
    def __init__(self, vocab, d_model, n_layers, n_heads, max_seq):
        super().__init__()
        self.embed = nn.Embedding(vocab, d_model)
        self.blocks = nn.ModuleList(TransformerBlock(d_model, n_heads) for _ in range(n_layers))
        self.norm_f = RMSNorm(d_model)

        cos, sin = build_rope_cache(max_seq, d_model // n_heads)
        self.register_buffer("cos", cos, persistent=False)
        self.register_buffer("sin", sin, persistent=False)

        self.apply(self._init_weights)
        for name, p in self.named_parameters():
            if name.endswith("wo.weight") or name.endswith("w_down.weight"):
                nn.init.normal_(p, mean=0.0, std=INIT_STD / math.sqrt(2 * n_layers))

    @staticmethod
    def _init_weights(module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=INIT_STD)

    def hidden_before_head(self, ids):
        """Everything up to but not including the output projection."""
        x = self.embed(ids)
        for block in self.blocks:
            x = block(x, self.cos, self.sin)
        return self.norm_f(x)

    def forward(self, ids):
        return self.hidden_before_head(ids) @ self.embed.weight.T


def lm_loss(logits, ids):
    """Next-token cross-entropy. Position t predicts token t+1."""
    vocab = logits.shape[-1]
    return F.cross_entropy(logits[:, :-1, :].reshape(-1, vocab), ids[:, 1:].reshape(-1))


# ==========================================================================
# HARNESS — reference implementations and probes. Do not edit.
# ==========================================================================


def ref_attention_module(module, x, cos, sin):
    """What Attention.forward should compute, built from torch primitives."""
    b, s, d = x.shape
    n_heads, head_dim = module.n_heads, module.head_dim

    def heads(t):
        return t.view(b, s, n_heads, head_dim).transpose(1, 2)

    q = heads(module.wq(x))
    k = heads(module.wk(x))
    v = heads(module.wv(x))

    def rope(t):
        cos_s, sin_s = cos[:s], sin[:s]
        t1, t2 = t[..., 0::2], t[..., 1::2]
        out = torch.empty_like(t)
        out[..., 0::2] = t1 * cos_s - t2 * sin_s
        out[..., 1::2] = t1 * sin_s + t2 * cos_s
        return out

    # RoPE on Q and K only.
    q, k = rope(q), rope(k)
    out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
    return module.wo(out.transpose(1, 2).contiguous().view(b, s, d))


def probe(results, name, ok, detail=""):
    results.append((name, bool(ok)))
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}")
    if detail:
        print(f"      {detail}", file=sys.stderr)


def main():
    torch.manual_seed(SEED)
    results = []

    print("=== Debug the transformer ===")
    print(f"vocab {VOCAB}  d_model {D_MODEL}  layers {N_LAYERS}  heads {N_HEADS}  head_dim {HEAD_DIM}")
    print()
    print("Probes run local to global. Fix the first failure, rerun, repeat.")

    print()
    print("--- 1. the causal mask ---")
    mask = causal_mask(6)
    expected_mask = torch.ones(6, 6, dtype=torch.bool).tril()
    probe(results, "mask is lower-triangular with the diagonal included",
          torch.equal(mask, expected_mask), f"got\n{mask.int()}")
    probe(results, "row i allows exactly i+1 keys",
          torch.equal(mask.sum(dim=1), torch.arange(1, 7)), f"row sums {mask.sum(dim=1).tolist()}")

    print()
    print("--- 2. head splitting ---")
    x = torch.randn(2, 5, D_MODEL)
    heads = split_heads(x, N_HEADS)
    probe(results, "split_heads gives (B, H, S, head_dim)", tuple(heads.shape) == (2, N_HEADS, 5, HEAD_DIM),
          f"got {tuple(heads.shape)}")
    probe(results, "merge_heads inverts split_heads", torch.allclose(merge_heads(heads), x, atol=EXACT_ATOL))
    head_2 = heads[:, 2]
    slice_2 = x[..., 2 * HEAD_DIM:3 * HEAD_DIM]
    probe(results, "head h holds feature channels [h*dh, (h+1)*dh)",
          torch.allclose(head_2, slice_2, atol=EXACT_ATOL),
          "if this fails, the view is carving up the sequence axis, not the feature axis")

    print()
    print("--- 3. the attention kernel ---")
    q = torch.randn(2, N_HEADS, 5, HEAD_DIM)
    k = torch.randn(2, N_HEADS, 5, HEAD_DIM)
    v = torch.randn(2, N_HEADS, 5, HEAD_DIM)
    full = torch.ones(5, 5, dtype=torch.bool)
    mine = attention(q, k, v, full)
    theirs = F.scaled_dot_product_attention(q, k, v, is_causal=False)
    diff = float((mine - theirs).abs().max())
    probe(results, "attention matches the fused kernel with an open mask",
          diff < FUSED_ATOL, f"max abs diff {diff:.3e} — a missing 1/sqrt(head_dim) shows up exactly here")

    print()
    print("--- 4. the attention module ---")
    model = TransformerLM(VOCAB, D_MODEL, N_LAYERS, N_HEADS, MAX_SEQ)
    xa = torch.randn(2, 7, D_MODEL)
    with torch.no_grad():
        got = model.blocks[0].attn(xa, model.cos, model.sin)
        want = ref_attention_module(model.blocks[0].attn, xa, model.cos, model.sin)
    diff = float((got - want).abs().max())
    probe(results, "Attention.forward matches the reference",
          diff < FUSED_ATOL, f"max abs diff {diff:.3e} — check what RoPE is applied to")

    print()
    print("--- 5. the final norm ---")
    ids = torch.randint(0, VOCAB, (BATCH, SEQ))
    with torch.no_grad():
        hidden = model.hidden_before_head(ids)
    rms = float(hidden.float().pow(2).mean(-1).sqrt().mean())
    probe(results, "hidden state entering the output head has RMS near 1",
          abs(rms - 1.0) < RMS_TOL, f"measured RMS {rms:.4f}")

    print()
    print("--- 6. the loss shift ---")
    crafted = torch.arange(6).repeat(1, 1) % VOCAB
    oracle_next = F.one_hot(torch.roll(crafted, shifts=-1, dims=1), VOCAB).float() * 30.0
    oracle_self = F.one_hot(crafted, VOCAB).float() * 30.0
    loss_next = float(lm_loss(oracle_next, crafted))
    loss_self = float(lm_loss(oracle_self, crafted))
    probe(results, "loss is ~0 for logits that predict the NEXT token",
          loss_next < 0.01, f"got {loss_next:.4f}")
    probe(results, "loss is large for logits that predict the CURRENT token",
          loss_self > 5.0, f"got {loss_self:.4f} — if this is ~0 the shift is missing")

    print()
    print("--- 7. the initialization check ---")
    with torch.no_grad():
        init_loss = float(lm_loss(model(ids), ids))
    expected = math.log(VOCAB)
    probe(results, f"initial loss is near ln(vocab) = {expected:.3f}",
          abs(init_loss - expected) < INIT_LOSS_TOL, f"got {init_loss:.4f}")

    print()
    print("--- 8. causality ---")
    with torch.no_grad():
        base = model(ids)
        bumped = ids.clone()
        bumped[:, SEQ - 3] = (bumped[:, SEQ - 3] + 191) % VOCAB
        after = model(bumped)
    delta = float((base[:, : SEQ - 3] - after[:, : SEQ - 3]).abs().max())
    probe(results, "changing a future token leaves earlier logits untouched",
          delta < EXACT_ATOL, f"max delta {delta:.3e}")

    print()
    print("--- 9. end to end: memorize a sequence ---")
    torch.manual_seed(SEED + 1)
    target = torch.randint(0, VOCAB, (1, MEMORIZE_LEN))
    opt = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.0)
    first_loss = None
    last_loss = None
    for step in range(TRAIN_STEPS):
        loss = lm_loss(model(target), target)
        opt.zero_grad()
        loss.backward()
        opt.step()
        last_loss = float(loss.detach())
        if first_loss is None:
            first_loss = last_loss
    print(f"  loss {first_loss:.4f} -> {last_loss:.4f} over {TRAIN_STEPS} steps")
    probe(results, "final loss below 0.05", last_loss < 0.05)

    with torch.no_grad():
        ids_gen = target[:, :1]
        for _ in range(MEMORIZE_LEN - 1):
            nxt = model(ids_gen[:, -MAX_SEQ:])[:, -1, :].argmax(dim=-1, keepdim=True)
            ids_gen = torch.cat([ids_gen, nxt], dim=1)
    matched = int((ids_gen[0] == target[0]).sum())
    probe(results, f"greedy decoding reproduces all {MEMORIZE_LEN} tokens", matched == MEMORIZE_LEN,
          f"matched {matched}")

    print()
    failed = [name for name, ok in results if not ok]
    print(f"probes passed: {len(results) - len(failed)} / {len(results)}")
    if failed:
        print(f"first failing probe: {failed[0]}")
    print(f"ALL CHECKS PASS: {not failed}")


if __name__ == "__main__":
    main()
