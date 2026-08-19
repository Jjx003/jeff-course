"""
A complete decoder-only language model: pre-norm blocks, RoPE, GQA-capable
attention, tied output head, shifted next-token loss, greedy generation.

Graded output goes to stdout in float32 with seed 0. Timings and exact
floating-point differences go to stderr, which is not graded.

Fill in the four TODO blocks. Everything else — attention, RMSNorm, SwiGLU,
RoPE, the initialization — is already built from the previous two modules.
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
N_KV_HEADS = 4
HEAD_DIM = D_MODEL // N_HEADS
MAX_SEQ = 64
ROPE_BASE = 10000.0
EPS = 1e-6
INIT_STD = 0.02

BATCH = 2
SEQ = 32
TRAIN_STEPS = 300
LEARNING_RATE = 3e-3
MEMORIZE_LEN = 24
INIT_LOSS_TOL = 0.25
EXACT_ATOL = 1e-6


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = EPS):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        dtype = x.dtype
        x32 = x.float()
        normed = x32 * torch.rsqrt(x32.pow(2).mean(-1, keepdim=True) + self.eps)
        return normed.to(dtype) * self.weight


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


class Attention(nn.Module):
    def __init__(self, d_model, n_heads, n_kv_heads):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.head_dim = d_model // n_heads
        self.n_rep = n_heads // n_kv_heads
        self.wq = nn.Linear(d_model, n_heads * self.head_dim, bias=False)
        self.wk = nn.Linear(d_model, n_kv_heads * self.head_dim, bias=False)
        self.wv = nn.Linear(d_model, n_kv_heads * self.head_dim, bias=False)
        self.wo = nn.Linear(n_heads * self.head_dim, d_model, bias=False)

    def forward(self, x, cos, sin):
        b, s, _ = x.shape

        q = self.wq(x).view(b, s, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.wk(x).view(b, s, self.n_kv_heads, self.head_dim).transpose(1, 2)
        v = self.wv(x).view(b, s, self.n_kv_heads, self.head_dim).transpose(1, 2)

        # RoPE on Q and K only. V carries content, not position.
        q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)

        k = k.repeat_interleave(self.n_rep, dim=1)
        v = v.repeat_interleave(self.n_rep, dim=1)

        scores = q @ k.transpose(-2, -1) / math.sqrt(self.head_dim)
        mask = torch.ones(s, s, dtype=torch.bool, device=x.device).tril()
        scores = scores.masked_fill(~mask, float("-inf"))
        out = scores.softmax(dim=-1) @ v

        out = out.transpose(1, 2).contiguous().view(b, s, -1)
        return self.wo(out)


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
    def __init__(self, d_model, n_heads, n_kv_heads):
        super().__init__()
        self.norm1 = RMSNorm(d_model)
        self.attn = Attention(d_model, n_heads, n_kv_heads)
        self.norm2 = RMSNorm(d_model)
        self.ffn = SwiGLU(d_model)

    def forward(self, x, cos, sin):
        """TODO 1: the pre-norm residual structure.

            x = x + attn(norm1(x))
            x = x + ffn(norm2(x))

        The residual adds the UNNORMALIZED x. Writing
        norm1(x) + attn(norm1(x)) still trains and is much worse — the point
        of pre-norm is that the residual stream is an unobstructed additive
        path from input to output.
        """
        raise NotImplementedError


class TransformerLM(nn.Module):
    def __init__(self, vocab, d_model, n_layers, n_heads, n_kv_heads, max_seq):
        super().__init__()
        self.embed = nn.Embedding(vocab, d_model)
        self.blocks = nn.ModuleList(
            TransformerBlock(d_model, n_heads, n_kv_heads) for _ in range(n_layers)
        )
        self.norm_f = RMSNorm(d_model)

        cos, sin = build_rope_cache(max_seq, d_model // n_heads)
        self.register_buffer("cos", cos, persistent=False)
        self.register_buffer("sin", sin, persistent=False)

        self.apply(self._init_weights)
        # GPT-2's residual scaling: 2L sublayers write into the stream, so
        # without this its variance grows linearly with depth.
        for name, p in self.named_parameters():
            if name.endswith("wo.weight") or name.endswith("w_down.weight"):
                nn.init.normal_(p, mean=0.0, std=INIT_STD / math.sqrt(2 * n_layers))

    @staticmethod
    def _init_weights(module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=INIT_STD)
            if isinstance(module, nn.Linear) and module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, ids):
        """TODO 2: embed, run the blocks, final norm, tied output head.

        Pass self.cos and self.sin down to each block. The final norm is
        mandatory in a pre-norm model: the residual stream's magnitude grows
        with depth, so without it the logits carry an arbitrary scale.

        Tie the head to the embedding: x @ self.embed.weight.T.
        """
        raise NotImplementedError


def hidden_state(model, ids):
    """Everything up to but not including the output projection.

    Harness-side, so the weight-tying check below can isolate the two paths
    into the tied tensor without depending on how you wrote forward().
    """
    x = model.embed(ids)
    for block in model.blocks:
        x = block(x, model.cos, model.sin)
    return model.norm_f(x)


def lm_loss(logits, ids):
    """Next-token cross-entropy. Position t predicts token t+1.

    TODO 3: drop the last position from the logits, drop the first token from
    the labels, flatten both, and call F.cross_entropy.

    F.cross_entropy does not shift anything for you — that is a persistent
    myth, and an interviewer may float it to see whether you know. Shift here
    or in the data loader, never in both.
    """
    raise NotImplementedError


@torch.no_grad()
def generate(model, prompt, max_new_tokens):
    """Greedy decoding, recomputing the full prefix each step (no cache).

    TODO 4: repeatedly run the model on the current ids, take the argmax of
    the LAST position's logits, and append it.

    Crop the context to the last MAX_SEQ tokens so the RoPE cache never runs
    off its end. A KV cache would make this O(1) per token instead of O(S);
    that is module 26.
    """
    raise NotImplementedError


def main():
    torch.manual_seed(SEED)

    model = TransformerLM(VOCAB, D_MODEL, N_LAYERS, N_HEADS, N_KV_HEADS, MAX_SEQ)
    n_params = sum(p.numel() for p in model.parameters())

    print("=== A whole language model ===")
    print(f"vocab: {VOCAB}  d_model: {D_MODEL}  layers: {N_LAYERS}  heads: {N_HEADS}  kv heads: {N_KV_HEADS}")
    print(f"parameters: {n_params}")
    print(f"12*L*d^2 estimate: {12 * N_LAYERS * D_MODEL * D_MODEL}")

    ids = torch.randint(0, VOCAB, (BATCH, SEQ))

    print()
    print("--- shapes ---")
    logits = model(ids)
    print(f"input ids: {tuple(ids.shape)}")
    print(f"logits: {tuple(logits.shape)}")
    print(f"logits shape is (B, S, V): {tuple(logits.shape) == (BATCH, SEQ, VOCAB)}")

    print()
    print("--- the initialization check ---")
    init_loss = float(lm_loss(logits, ids).detach())
    expected = math.log(VOCAB)
    print(f"initial loss: {init_loss:.4f}")
    print(f"ln(vocab): {expected:.4f}")
    print(f"within {INIT_LOSS_TOL} of ln(vocab): {abs(init_loss - expected) < INIT_LOSS_TOL}")

    print()
    print("--- weight tying ---")
    # The tied tensor sits on two paths: the embedding lookup and the output
    # projection. Isolate each by detaching the other, then check the tied
    # gradient is their sum -- the branch-sum rule, in production code.
    model.zero_grad()
    lm_loss(model(ids), ids).backward()
    tied_grad = model.embed.weight.grad.clone()

    model.zero_grad()
    # Head path only: the hidden state is cut off, so nothing reaches the
    # embedding through the lookup.
    lm_loss(hidden_state(model, ids).detach() @ model.embed.weight.T, ids).backward()
    head_path = model.embed.weight.grad.clone()

    model.zero_grad()
    # Embedding path only: the output projection uses a detached copy, so the
    # gradient can only arrive through the lookup.
    frozen_head = model.embed.weight.detach().clone()
    lm_loss(hidden_state(model, ids) @ frozen_head.T, ids).backward()
    embed_path = model.embed.weight.grad.clone()

    paths_sum = bool(torch.allclose(tied_grad, head_path + embed_path, atol=1e-5))
    both_paths = bool(head_path.abs().max() > 0 and embed_path.abs().max() > 0)
    print(f"gradient shape matches the tensor: {tuple(tied_grad.shape) == tuple(model.embed.weight.shape)}")
    print(f"both paths carry gradient: {both_paths}")
    print(f"tied gradient equals the sum of the two paths: {paths_sum}")
    print(f"  |tied| {float(tied_grad.norm()):.4f}  |head| {float(head_path.norm()):.4f}"
          f"  |embed| {float(embed_path.norm()):.4f}", file=sys.stderr)

    print()
    print("--- causality ---")
    with torch.no_grad():
        base = model(ids)
        bumped = ids.clone()
        bumped[:, SEQ - 4] = (bumped[:, SEQ - 4] + 137) % VOCAB
        after = model(bumped)
    delta = float((base[:, : SEQ - 4] - after[:, : SEQ - 4]).abs().max())
    print(f"changing token {SEQ - 4} leaves earlier logits untouched: {delta < EXACT_ATOL}")
    print(f"  max delta: {delta:.3e}", file=sys.stderr)

    print()
    print("--- can it memorize one sequence? ---")
    torch.manual_seed(SEED + 1)
    target = torch.randint(0, VOCAB, (1, MEMORIZE_LEN))
    opt = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.0)
    losses = []
    for step in range(TRAIN_STEPS):
        loss = lm_loss(model(target), target)
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(float(loss.detach()))
        if step % 100 == 0:
            print(f"  step {step:>3}: loss {losses[-1]:.4f}")
    print(f"  step {TRAIN_STEPS}: loss {losses[-1]:.4f}")
    print(f"final loss below 0.05: {losses[-1] < 0.05}")
    print(f"loss fell by more than 10x: {losses[0] / max(losses[-1], 1e-9) > 10}")

    print()
    print("--- the loss shift, tested on the memorized sequence ---")
    with torch.no_grad():
        trained_logits = model(target)
        aligned = float(lm_loss(trained_logits, target))
        rolled = torch.roll(target, shifts=1, dims=1)
        misaligned = float(lm_loss(trained_logits, rolled))
    print(f"loss with the correct shift: {aligned:.4f}")
    print(f"loss with the labels rolled by one: {misaligned:.4f}")
    print(f"misaligned labels are much worse: {misaligned > aligned + 3.0}")

    print()
    print("--- greedy generation reproduces it ---")
    generated = generate(model, target[:, :1], MEMORIZE_LEN - 1)
    matched = int((generated[0] == target[0]).sum())
    print(f"tokens reproduced from a 1-token prompt: {matched} / {MEMORIZE_LEN}")
    print(f"reproduced exactly: {matched == MEMORIZE_LEN}")

    print()
    all_ok = (
        tuple(logits.shape) == (BATCH, SEQ, VOCAB)
        and abs(init_loss - expected) < INIT_LOSS_TOL
        and delta < EXACT_ATOL
        and losses[-1] < 0.05
        and misaligned > aligned + 3.0
        and matched == MEMORIZE_LEN
        and paths_sum
        and both_paths
    )
    print(f"ALL CHECKS PASS: {all_ok}")


if __name__ == "__main__":
    main()
