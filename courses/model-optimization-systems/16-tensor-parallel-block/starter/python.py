"""
Tensor parallelism for one transformer block on simulated devices.

Everything runs on CPU. The "devices" are entries of a Python list; the
"collective" is a function you write that sums their partial results and
keeps honest books about the traffic. See problem.md for the required
output format — the grader compares printed stdout.
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

        TODO 1: assert there are exactly `tp` partials, increment `calls`,
        add one rank's buffer size (numel * element_size) to `payload_bytes`,
        and return the elementwise sum of the partials.
        """
        raise NotImplementedError

    def ring_bytes_per_gpu(self) -> int:
        # TODO 2: ring all-reduce moves 2(p-1)/p * payload through each
        # GPU's links. Return that, as an int.
        raise NotImplementedError


def shard_columns(weight: torch.Tensor, tp: int) -> list[torch.Tensor]:
    """Column-parallel shards of an (out_features, in_features) weight.

    TODO 3: column parallelism splits the *output* features. For the
    nn.Linear convention y = x @ W.T, that is a chunk along dim 0.
    """
    raise NotImplementedError


def shard_rows(weight: torch.Tensor, tp: int) -> list[torch.Tensor]:
    """Row-parallel shards: split the *input* features.

    TODO 4: chunk along dim 1.
    """
    raise NotImplementedError


def reference_mlp(x: torch.Tensor, w_up: torch.Tensor, w_down: torch.Tensor,
                  act) -> torch.Tensor:
    return act(x @ w_up.T) @ w_down.T


def tp_mlp(x: torch.Tensor, w_up: torch.Tensor, w_down: torch.Tensor,
           act, ledger: CommLedger) -> torch.Tensor:
    """Megatron-style MLP: column-cut W_up, row-cut W_down, one all-reduce.

    TODO 5: for each rank, compute the local activation
    act(x @ up_shard.T) — shape (B, S, FFN/p) — then the partial output
    h_local @ down_shard.T. Collect the partials and make exactly one
    call to ledger.all_reduce. Nothing else may communicate.
    """
    raise NotImplementedError


def wrong_cut_mlp(x: torch.Tensor, w_up: torch.Tensor, w_down: torch.Tensor,
                  act, tp: int) -> torch.Tensor:
    """Row-cut W_up and skip the pre-activation all-reduce.

    TODO 6: split x along its last dimension and W_up along dim 1, apply
    `act` to each rank's *partial* pre-activation, sum the activated
    partials, then multiply by the full W_down. This is deliberately the
    wrong function — main() measures how wrong.
    """
    raise NotImplementedError


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
    """Head-sharded attention: column-cut QKV, row-cut W_o, one all-reduce.

    TODO 7: column-shard w_q, w_k, w_v and row-shard w_o. Each rank owns
    Q_HEADS // tp query heads and KV_HEADS // tp KV heads: project with its
    shards, run `attention` on the local heads only, flatten heads back
    into the feature dimension, and multiply by its w_o row-shard to get a
    partial sum. One ledger.all_reduce at the end.
    """
    raise NotImplementedError


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
        # TODO 8: mem_ms is the per-GPU weight read time (each GPU streams
        # its 1/tp shard); comm_ms is `collectives * ALPHA_ALLREDUCE` for
        # tp > 1 and 0.0 at tp == 1; step_ms is their sum. `base` is the
        # tp == 1 step time, so speedup = base / step_ms.
        mem_ms = 0.0
        comm_ms = 0.0
        step_ms = 0.0
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
