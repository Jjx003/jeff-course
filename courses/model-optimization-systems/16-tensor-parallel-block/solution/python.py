"""
Reference solution for module 16.

Tensor parallelism for one transformer block on simulated devices: column- and
row-parallel sharding, a communication ledger, an exact-arithmetic certificate,
the wrong cut measured, and the collective cost at 70B scale.
"""

import torch
import torch.nn.functional as F

BATCH = 2
SEQ = 6
HIDDEN = 256
FFN = 1024
Q_HEADS = 8
KV_HEADS = 4
HEAD_DIM = 32
TP = 4

# 70B-scale constants for the analytic table (same machine as module 2).
PARAMS = 70e9
WEIGHT_BYTES = 2.0  # BF16
HBM_PER_GPU = 3350e9  # bytes/s
LAYERS_70B = 80
ALPHA_ALLREDUCE = 10e-6  # seconds per small NVLink all-reduce (measured-scale)


class CommLedger:
    """Counts collective calls and the bytes they move."""

    def __init__(self, tp: int) -> None:
        self.tp = tp
        self.calls = 0
        self.payload_bytes = 0

    def all_reduce(self, partials: list[torch.Tensor]) -> torch.Tensor:
        """Sum per-rank partial results and record the traffic.

        The payload is one rank's buffer; ring all-reduce moves
        2(p-1)/p * payload through each GPU's links.
        """
        assert len(partials) == self.tp
        self.calls += 1
        self.payload_bytes += partials[0].numel() * partials[0].element_size()
        total = partials[0].clone()
        for part in partials[1:]:
            total = total + part
        return total

    def ring_bytes_per_gpu(self) -> int:
        return int(2 * (self.tp - 1) / self.tp * self.payload_bytes)


def shard_columns(weight: torch.Tensor, tp: int) -> list[torch.Tensor]:
    """Column-parallel shards of an (out_features, in_features) weight.

    Column parallelism splits the *output* features, which for the
    nn.Linear convention y = x @ W.T means splitting along dim 0.
    """
    return list(torch.chunk(weight, tp, dim=0))


def shard_rows(weight: torch.Tensor, tp: int) -> list[torch.Tensor]:
    """Row-parallel shards: split the *input* features, dim 1."""
    return list(torch.chunk(weight, tp, dim=1))


def reference_mlp(x: torch.Tensor, w_up: torch.Tensor, w_down: torch.Tensor,
                  act) -> torch.Tensor:
    return act(x @ w_up.T) @ w_down.T


def tp_mlp(x: torch.Tensor, w_up: torch.Tensor, w_down: torch.Tensor,
           act, ledger: CommLedger) -> torch.Tensor:
    """Megatron-style MLP: column-cut W_up, row-cut W_down, one all-reduce."""
    up_shards = shard_columns(w_up, ledger.tp)
    down_shards = shard_rows(w_down, ledger.tp)
    partials = []
    for rank in range(ledger.tp):
        h_local = act(x @ up_shards[rank].T)          # (B, S, FFN/p), local
        partials.append(h_local @ down_shards[rank].T)  # partial sum of output
    return ledger.all_reduce(partials)


def wrong_cut_mlp(x: torch.Tensor, w_up: torch.Tensor, w_down: torch.Tensor,
                  act, tp: int) -> torch.Tensor:
    """Row-cut W_up and skip the pre-activation all-reduce.

    Each rank holds a *partial sum* of the pre-activation. Applying the
    nonlinearity to partial sums and summing afterwards is not the same
    function, because act(a) + act(b) != act(a + b).
    """
    up_row_shards = shard_rows(w_up, tp)
    x_shards = list(torch.chunk(x, tp, dim=-1))
    h = torch.zeros(x.shape[:-1] + (w_up.shape[0],), dtype=x.dtype)
    for rank in range(tp):
        h = h + act(x_shards[rank] @ up_row_shards[rank].T)
    return h @ w_down.T


def attention(q: torch.Tensor, k: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
    """Plain causal attention over (B, H, S, D) tensors with GQA broadcast."""
    group = q.shape[1] // k.shape[1]
    k = k.repeat_interleave(group, dim=1)
    v = v.repeat_interleave(group, dim=1)
    scores = q @ k.transpose(-2, -1) / (q.shape[-1] ** 0.5)
    mask = torch.triu(torch.ones(q.shape[-2], q.shape[-2], dtype=torch.bool), 1)
    scores = scores.masked_fill(mask, float("-inf"))
    return torch.softmax(scores, dim=-1) @ v


def split_heads(x: torch.Tensor, heads: int) -> torch.Tensor:
    b, s, _ = x.shape
    return x.view(b, s, heads, -1).transpose(1, 2)  # (B, H, S, D)


def reference_attention_block(x, w_q, w_k, w_v, w_o) -> torch.Tensor:
    q = split_heads(x @ w_q.T, Q_HEADS)
    k = split_heads(x @ w_k.T, KV_HEADS)
    v = split_heads(x @ w_v.T, KV_HEADS)
    out = attention(q, k, v)                       # (B, Hq, S, D)
    out = out.transpose(1, 2).reshape(x.shape[0], x.shape[1], -1)
    return out @ w_o.T


def tp_attention_block(x, w_q, w_k, w_v, w_o, ledger: CommLedger) -> torch.Tensor:
    """Head-sharded attention: column-cut QKV, row-cut W_o, one all-reduce."""
    q_shards = shard_columns(w_q, ledger.tp)
    k_shards = shard_columns(w_k, ledger.tp)
    v_shards = shard_columns(w_v, ledger.tp)
    o_shards = shard_rows(w_o, ledger.tp)
    q_per_rank = Q_HEADS // ledger.tp
    kv_per_rank = KV_HEADS // ledger.tp
    partials = []
    for rank in range(ledger.tp):
        q = split_heads(x @ q_shards[rank].T, q_per_rank)
        k = split_heads(x @ k_shards[rank].T, kv_per_rank)
        v = split_heads(x @ v_shards[rank].T, kv_per_rank)
        out = attention(q, k, v)                   # local heads only
        out = out.transpose(1, 2).reshape(x.shape[0], x.shape[1], -1)
        partials.append(out @ o_shards[rank].T)    # partial sum of projection
    return ledger.all_reduce(partials)


def collective_cost_table() -> None:
    """Decode-step floors for a 70B model across TP degrees."""
    total_weight_bytes = PARAMS * WEIGHT_BYTES
    collectives = 2 * LAYERS_70B
    print("--- what the collectives cost at 70B scale ---")
    print("(80 layers, 2 all-reduces/layer, alpha = 10 us, batch 1 decode)")
    header = f"{'tp':>3} {'GB/gpu':>8} {'mem ms':>8} {'comm ms':>8} {'step ms':>8} {'speedup':>8}"
    print(header)
    base = None
    for tp in [1, 2, 4, 8]:
        mem_ms = total_weight_bytes / (tp * HBM_PER_GPU) * 1e3
        comm_ms = collectives * ALPHA_ALLREDUCE * 1e3 if tp > 1 else 0.0
        step_ms = mem_ms + comm_ms
        if base is None:
            base = step_ms
        print(
            f"{tp:>3} {total_weight_bytes / tp / 1e9:>8.1f} {mem_ms:>8.2f} "
            f"{comm_ms:>8.2f} {step_ms:>8.2f} {base / step_ms:>7.2f}x"
        )
    print()


def main() -> None:
    torch.manual_seed(0)

    x = torch.randn(BATCH, SEQ, HIDDEN)
    w_up = torch.randn(FFN, HIDDEN) / HIDDEN ** 0.5
    w_down = torch.randn(HIDDEN, FFN) / FFN ** 0.5
    w_q = torch.randn(Q_HEADS * HEAD_DIM, HIDDEN) / HIDDEN ** 0.5
    w_k = torch.randn(KV_HEADS * HEAD_DIM, HIDDEN) / HIDDEN ** 0.5
    w_v = torch.randn(KV_HEADS * HEAD_DIM, HIDDEN) / HIDDEN ** 0.5
    w_o = torch.randn(HIDDEN, Q_HEADS * HEAD_DIM) / (Q_HEADS * HEAD_DIM) ** 0.5

    print("=== Tensor parallelism on simulated devices ===")
    print(
        f"config: batch={BATCH} seq={SEQ} hidden={HIDDEN} ffn={FFN} "
        f"q_heads={Q_HEADS} kv_heads={KV_HEADS} head_dim={HEAD_DIM} tp={TP}"
    )
    print()

    print("--- sharding round-trip ---")
    col = shard_columns(w_up, TP)
    row = shard_rows(w_down, TP)
    print(f"column shards of W_up: {TP} x {tuple(col[0].shape)}")
    print(f"row shards of W_down: {TP} x {tuple(row[0].shape)}")
    col_ok = torch.equal(torch.cat(col, dim=0), w_up)
    row_ok = torch.equal(torch.cat(row, dim=1), w_down)
    print(f"reassembled == original: {col_ok and row_ok}")
    print()

    print("--- TP MLP forward ---")
    ledger = CommLedger(TP)
    ref = reference_mlp(x, w_up, w_down, F.gelu)
    tp_out = tp_mlp(x, w_up, w_down, F.gelu, ledger)
    mlp_close = torch.allclose(tp_out, ref, atol=1e-5)
    print(f"all-reduces: {ledger.calls}")
    print(f"payload per all-reduce: {ledger.payload_bytes} bytes")
    print(f"ring bytes per GPU: {ledger.ring_bytes_per_gpu()}")
    print(f"max |tp - ref| < 1e-5: {mlp_close}")
    print()

    print("--- exact-arithmetic certificate (integer tensors, float64, ReLU) ---")
    xi = torch.randint(-4, 5, (BATCH, SEQ, HIDDEN)).to(torch.float64)
    wui = torch.randint(-4, 5, (FFN, HIDDEN)).to(torch.float64)
    wdi = torch.randint(-4, 5, (HIDDEN, FFN)).to(torch.float64)
    int_ledger = CommLedger(TP)
    ref_int = reference_mlp(xi, wui, wdi, F.relu)
    tp_int = tp_mlp(xi, wui, wdi, F.relu, int_ledger)
    exact = torch.equal(tp_int, ref_int)
    print(f"bit-exact equal: {exact}")
    print("(integer values stay exact in float64, so the only possible")
    print(" difference is the cut itself. There is none: the cut is algebra,")
    print(" and the fp32 residual above is summation-order rounding.)")
    print()

    print("--- TP attention forward (GQA) ---")
    attn_ledger = CommLedger(TP)
    ref_attn = reference_attention_block(x, w_q, w_k, w_v, w_o)
    tp_attn = tp_attention_block(x, w_q, w_k, w_v, w_o, attn_ledger)
    attn_close = torch.allclose(tp_attn, ref_attn, atol=1e-5)
    print(f"q heads per rank: {Q_HEADS // TP}, kv heads per rank: {KV_HEADS // TP}")
    print(f"all-reduces: {attn_ledger.calls}")
    print(f"max |tp - ref| < 1e-5: {attn_close}")
    print()

    print("--- full block ---")
    block_ledger = CommLedger(TP)
    a = tp_attention_block(x, w_q, w_k, w_v, w_o, block_ledger)
    _ = tp_mlp(x + a, w_up, w_down, F.gelu, block_ledger)
    print(f"all-reduces per layer: {block_ledger.calls}")
    print()

    print("--- the wrong cut: row-parallel W_up, no pre-activation all-reduce ---")
    wrong = wrong_cut_mlp(x, w_up, w_down, F.gelu, TP)
    rel_err = (torch.linalg.norm(wrong - ref) / torch.linalg.norm(ref)).item()
    print(f"relative error: {rel_err:.4f}")
    print("(gelu(a) + gelu(b) != gelu(a + b): partial sums must be reduced")
    print(" before any nonlinearity, which would double the collectives.)")
    print()

    collective_cost_table()

    assert col_ok and row_ok
    assert mlp_close and attn_close
    assert exact
    assert block_ledger.calls == 2
    assert rel_err > 0.1
    print("=== all checks passed ===")


if __name__ == "__main__":
    main()
