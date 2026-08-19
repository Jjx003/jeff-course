"""
KV-cached generation and the sampling strategies that go with it.

Correctness here means one thing: cached generation must produce EXACTLY the
same tokens as uncached generation. Everything else is an optimization on top
of that invariant.

Graded output goes to stdout with seed 0. Timings and float differences go to
stderr, which is not graded.

Fill in the six TODO blocks.
"""

import math
import sys
import time

import torch
import torch.nn as nn
import torch.nn.functional as F

SEED = 0
VOCAB = 256
D_MODEL = 64
N_LAYERS = 4
N_HEADS = 8
N_KV_HEADS = 2
HEAD_DIM = D_MODEL // N_HEADS
MAX_SEQ = 256
ROPE_BASE = 10000.0
EPS = 1e-6

PROMPT_LEN = 16
NEW_TOKENS = 48
EXACT_ATOL = 1e-5
SAMPLE_TRIALS = 20000


# ── Model ────────────────────────────────────────────────────────────────


class RMSNorm(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        x32 = x.float()
        return (x32 * torch.rsqrt(x32.pow(2).mean(-1, keepdim=True) + EPS)).to(x.dtype) * self.weight


def build_rope_cache(seq_len, head_dim):
    inv_freq = 1.0 / (ROPE_BASE ** (torch.arange(0, head_dim, 2).float() / head_dim))
    freqs = torch.outer(torch.arange(seq_len).float(), inv_freq)
    return freqs.cos(), freqs.sin()


def apply_rope(x, cos, sin, offset):
    """Rotate positions [offset, offset + S). The offset is what a cache needs."""
    seq = x.shape[-2]
    cos_s, sin_s = cos[offset:offset + seq], sin[offset:offset + seq]
    x1, x2 = x[..., 0::2], x[..., 1::2]
    out = torch.empty_like(x)
    out[..., 0::2] = x1 * cos_s - x2 * sin_s
    out[..., 1::2] = x1 * sin_s + x2 * cos_s
    return out


class Attention(nn.Module):
    def __init__(self):
        super().__init__()
        self.wq = nn.Linear(D_MODEL, N_HEADS * HEAD_DIM, bias=False)
        self.wk = nn.Linear(D_MODEL, N_KV_HEADS * HEAD_DIM, bias=False)
        self.wv = nn.Linear(D_MODEL, N_KV_HEADS * HEAD_DIM, bias=False)
        self.wo = nn.Linear(N_HEADS * HEAD_DIM, D_MODEL, bias=False)
        self.n_rep = N_HEADS // N_KV_HEADS

    def forward(self, x, cos, sin, layer_cache=None, offset=0):
        b, s, _ = x.shape

        """TODO 1: cached attention. Return (output, new_cache).

        Project and split heads as usual - q into N_HEADS, k and v into
        N_KV_HEADS.

        Then apply RoPE to q and k at the ABSOLUTE position, using the offset
        argument. This is the whole module: during decode the query tensor has
        sequence length 1, so its internal index is 0, and rotating by 0 tells
        every generated token it is the first token in the sequence. It runs.
        It is wrong.

        If layer_cache holds past keys and values, concatenate along dim=2
        (the sequence axis) BEFORE the repeat_interleave to N_HEADS - store G
        heads, expand on read, or GQA saves you nothing. Return the
        concatenated (k, v) as the new cache.

        Scores, scale, and softmax as usual. For the mask: with a query block
        of length s at the end of a key sequence of length T,

            mask = torch.ones(s, T, dtype=torch.bool).tril(diagonal=T - s)

        which reduces to a plain tril when s == T and to all-ones when s == 1.
        Skip it entirely when s == 1.
        """
        raise NotImplementedError


class SwiGLU(nn.Module):
    def __init__(self):
        super().__init__()
        hidden = (8 * D_MODEL) // 3
        self.w_gate = nn.Linear(D_MODEL, hidden, bias=False)
        self.w_up = nn.Linear(D_MODEL, hidden, bias=False)
        self.w_down = nn.Linear(hidden, D_MODEL, bias=False)

    def forward(self, x):
        return self.w_down(F.silu(self.w_gate(x)) * self.w_up(x))


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.norm1, self.attn = RMSNorm(D_MODEL), Attention()
        self.norm2, self.ffn = RMSNorm(D_MODEL), SwiGLU()

    def forward(self, x, cos, sin, layer_cache=None, offset=0):
        attn_out, new_cache = self.attn(self.norm1(x), cos, sin, layer_cache, offset)
        x = x + attn_out
        x = x + self.ffn(self.norm2(x))
        return x, new_cache


class TinyLM(nn.Module):
    def __init__(self):
        super().__init__()
        self.embed = nn.Embedding(VOCAB, D_MODEL)
        self.blocks = nn.ModuleList(Block() for _ in range(N_LAYERS))
        self.norm_f = RMSNorm(D_MODEL)
        cos, sin = build_rope_cache(MAX_SEQ, HEAD_DIM)
        self.register_buffer("cos", cos, persistent=False)
        self.register_buffer("sin", sin, persistent=False)

    def forward(self, ids, cache=None, offset=0):
        x = self.embed(ids)
        new_cache = []
        for i, block in enumerate(self.blocks):
            layer_cache = cache[i] if cache is not None else None
            x, updated = block(x, self.cos, self.sin, layer_cache, offset)
            new_cache.append(updated)
        return self.norm_f(x) @ self.embed.weight.T, new_cache


# ── Generation ───────────────────────────────────────────────────────────


@torch.no_grad()
def generate_uncached(model, prompt, n_new):
    """Recompute the whole prefix every step. O(n^2) forward passes of work."""
    ids = prompt
    for _ in range(n_new):
        logits, _ = model(ids)
        ids = torch.cat([ids, logits[:, -1:].argmax(dim=-1)], dim=1)
    return ids


@torch.no_grad()
def generate_cached(model, prompt, n_new):
    """Prefill once, then feed one token at a time with a growing cache.

    TODO 2:
      - prefill with the whole prompt at offset 0, seeding the cache with
        [(None, None)] * N_LAYERS
      - take the argmax of the last position as the first new token
      - then loop: append it to ids, run the model on that single token with
        the current cache and offset = ids.shape[1] - 1, take the new argmax

    The offset is the absolute position of the token being fed in, which is
    the number of tokens already in the cache.
    """
    raise NotImplementedError


# ── Sampling ─────────────────────────────────────────────────────────────


def apply_temperature(logits, temperature):
    """T < 1 sharpens, T > 1 flattens, T -> 0 approaches greedy.

    TODO 3: divide the logits by the temperature, with a special case for
    T <= 0 (you cannot divide by zero; return a one-hot at the argmax).

    The one-hot has to be per row. Indexing with a (B,) tensor of argmaxes
    sets those columns in every row, which is invisible at batch 1 and wrong
    above it -- and the test below runs at batch 2.
    """
    raise NotImplementedError


def top_k_filter(logits, k):
    """Keep the k highest logits, mask the rest to -inf.

    TODO 4: take the k-th largest logit as a threshold and mask everything
    below it. Return logits unchanged when k is 0 or at least the vocabulary
    size. Use a strict comparison so exact ties are kept.
    """
    raise NotImplementedError


def top_p_filter(logits, p):
    """Keep the smallest set of tokens whose cumulative probability reaches p.

    TODO 5: sort descending, take the softmax and its cumsum, then mark for
    removal every token whose cumulative mass BEFORE it already reaches p:

        remove = cumulative - probs >= p

    Two details the tests check. First, subtracting the token's own
    probability is what keeps the token that CROSSES the threshold - comparing
    cumulative >= p directly would retain strictly less than p of the mass.
    Second, force index 0 to survive, or a distribution whose top token
    already exceeds p loses everything and the softmax returns nan.

    Scatter the removal mask back to the original ordering before applying it.
    """
    raise NotImplementedError


def sample(logits, temperature=1.0, top_k=0, top_p=1.0, generator=None):
    """Penalties, then temperature, then truncation, then renormalize.

    TODO 6: apply the three filters in that order, softmax, and draw one
    sample with torch.multinomial (passing the generator through, so the test
    is reproducible).

    The order matters: temperature reshapes the distribution, so a top-p
    cutoff computed before it would be measuring a distribution you are not
    going to sample from.
    """
    raise NotImplementedError


# ── Report ───────────────────────────────────────────────────────────────


def main():
    torch.manual_seed(SEED)
    torch.set_grad_enabled(False)

    model = TinyLM().eval()
    prompt = torch.randint(0, VOCAB, (1, PROMPT_LEN))

    print("=== KV-cached generation and sampling ===")
    print(f"vocab {VOCAB}  d_model {D_MODEL}  layers {N_LAYERS}  heads {N_HEADS}  kv heads {N_KV_HEADS}")
    print(f"prompt {PROMPT_LEN} tokens, generating {NEW_TOKENS}")

    print()
    print("--- 1. cached generation is exact ---")
    t0 = time.perf_counter()
    slow = generate_uncached(model, prompt, NEW_TOKENS)
    t1 = time.perf_counter()
    fast = generate_cached(model, prompt, NEW_TOKENS)
    t2 = time.perf_counter()
    print(f"uncached output length: {slow.shape[1]}")
    print(f"cached output length: {fast.shape[1]}")
    print(f"token sequences are identical: {bool(torch.equal(slow, fast))}")
    print(f"  uncached {t1 - t0:.3f}s   cached {t2 - t1:.3f}s", file=sys.stderr)

    print()
    print("--- 2. the cache holds what it should ---")
    empty = [(None, None) for _ in range(N_LAYERS)]
    _, cache = model(prompt, cache=empty, offset=0)
    k0, v0 = cache[0]
    print(f"layers cached: {len(cache)}")
    print(f"K shape after prefill: {tuple(k0.shape)}")
    print(f"K has one entry per prompt token: {k0.shape[2] == PROMPT_LEN}")
    print(f"K is stored with {N_KV_HEADS} KV heads, not {N_HEADS}: {k0.shape[1] == N_KV_HEADS}")
    _, cache2 = model(prompt[:, :1], cache=cache, offset=PROMPT_LEN)
    print(f"one more token grows the cache by one: {cache2[0][0].shape[2] == PROMPT_LEN + 1}")

    bytes_per_token = 2 * N_KV_HEADS * HEAD_DIM * 2 * N_LAYERS
    print(f"bytes per token for this model (bf16): {bytes_per_token}")
    print(f"same formula at 80 layers, 8 kv heads, head_dim 128: {2 * 8 * 128 * 2 * 80} bytes/token")

    print()
    print("--- 3. RoPE offset matters ---")
    _, cache3 = model(prompt, cache=[(None, None) for _ in range(N_LAYERS)], offset=0)
    next_tok = prompt[:, :1]
    right, _ = model(next_tok, cache=cache3, offset=PROMPT_LEN)
    wrong, _ = model(next_tok, cache=cache3, offset=0)
    gap = float((right - wrong).abs().max())
    print(f"offset 0 gives different logits from offset {PROMPT_LEN}: {gap > EXACT_ATOL}")
    print("(a cached decoder that forgets the offset places every generated")
    print(" token at position 0 - it runs, and it is wrong)")
    print(f"  max logit gap {gap:.3e}", file=sys.stderr)

    print()
    print("--- 4. temperature ---")
    logits = torch.tensor([[4.0, 3.0, 2.0, 1.0, 0.0]])
    for temp in (0.5, 1.0, 2.0):
        probs = apply_temperature(logits, temp).softmax(dim=-1)
        top = float(probs[0, 0])
        entropy = float(-(probs * probs.clamp_min(1e-12).log()).sum())
        print(f"  T={temp:<4} top prob {top:.4f}  entropy {entropy:.4f}")
    sharp = apply_temperature(logits, 0.5).softmax(dim=-1)[0, 0]
    flat = apply_temperature(logits, 2.0).softmax(dim=-1)[0, 0]
    print(f"lower temperature concentrates mass: {bool(sharp > flat)}")

    # T = 0 has to be per-row, which only a batched input can catch.
    batched = torch.tensor([[1.0, 5.0, 2.0], [7.0, 0.0, 1.0]])
    greedy = apply_temperature(batched, 0.0).softmax(dim=-1)
    per_row_onehot = bool(
        torch.equal(greedy.argmax(dim=-1), batched.argmax(dim=-1))
        and torch.allclose(greedy.max(dim=-1).values, torch.ones(2))
    )
    print(f"T=0 is one-hot per row, not shared across the batch: {per_row_onehot}")
    print(f"argmax is unchanged by temperature: "
          f"{int(apply_temperature(logits, 0.5).argmax()) == int(apply_temperature(logits, 2.0).argmax())}")

    print()
    print("--- 5. top-k ---")
    for k in (1, 3, 5):
        kept = int(torch.isfinite(top_k_filter(logits, k)).sum())
        print(f"  k={k}: tokens kept {kept}")
    print(f"top-k keeps exactly k tokens: "
          f"{all(int(torch.isfinite(top_k_filter(logits, k)).sum()) == k for k in (1, 2, 3, 4, 5))}")
    print(f"top-k probabilities renormalize to 1: "
          f"{bool(torch.allclose(top_k_filter(logits, 3).softmax(-1).sum(), torch.tensor(1.0), atol=EXACT_ATOL))}")

    print()
    print("--- 6. top-p adapts to the distribution ---")
    confident = torch.tensor([[10.0, 1.0, 0.5, 0.2, 0.0]])
    uncertain = torch.tensor([[1.0, 0.95, 0.9, 0.85, 0.8]])
    for name, dist in (("confident", confident), ("uncertain", uncertain)):
        kept = int(torch.isfinite(top_p_filter(dist, 0.9)).sum())
        print(f"  {name:<10} distribution, top-p 0.9 keeps {kept} tokens")
    kept_conf = int(torch.isfinite(top_p_filter(confident, 0.9)).sum())
    kept_unc = int(torch.isfinite(top_p_filter(uncertain, 0.9)).sum())
    print(f"nucleus is smaller when the model is confident: {kept_conf < kept_unc}")
    print("(a fixed k cannot do this - it is the whole argument for top-p)")
    print(f"top-p always keeps at least one token: "
          f"{int(torch.isfinite(top_p_filter(confident, 0.01)).sum()) >= 1}")

    print()
    print("--- 7. sampling actually follows the filtered distribution ---")
    gen = torch.Generator().manual_seed(SEED)
    draws = torch.cat([
        sample(logits, temperature=1.0, top_k=3, generator=gen) for _ in range(SAMPLE_TRIALS)
    ])
    counts = torch.bincount(draws.flatten(), minlength=5).float() / SAMPLE_TRIALS
    expected = top_k_filter(logits, 3).softmax(dim=-1)[0]
    print(f"empirical frequencies over {SAMPLE_TRIALS} draws vs expected:")
    for i in range(5):
        print(f"  token {i}: empirical {float(counts[i]):.4f}  expected {float(expected[i]):.4f}")
    print(f"masked tokens are never drawn: {bool((counts[3:] == 0).all())}")
    print(f"frequencies match within 0.02: {bool((counts - expected).abs().max() < 0.02)}")

    print()
    all_ok = (
        bool(torch.equal(slow, fast))
        and k0.shape[2] == PROMPT_LEN
        and k0.shape[1] == N_KV_HEADS
        and gap > EXACT_ATOL
        and kept_conf < kept_unc
        and bool((counts[3:] == 0).all())
        and bool((counts - expected).abs().max() < 0.02)
        and per_row_onehot
    )
    print(f"ALL CHECKS PASS: {all_ok}")


if __name__ == "__main__":
    main()
