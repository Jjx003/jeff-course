"""
Tiled attention with the online softmax recurrence, checked against a naive
reference and against torch's own fused kernel.

Graded output goes to stdout and runs on CPU in float32 with seed 0 so that
your numbers match the grader exactly. Wall-clock timings and the exact
floating-point differences go to stderr, which is not graded, because both
depend on the BLAS reduction order of whatever machine you are on.
"""

import math
import sys
import time

import torch
import torch.nn.functional as F

BATCH = 2
HEADS = 4
SEQ = 256
HEAD_DIM = 64
KV_TILE = 64
Q_TILE = 64
MEMORY_SWEEP = [1024, 4096, 16384, 65536]
RTOL = 1e-5
ATOL = 1e-6
DIFF_THRESHOLD = 1e-5
TIMING_REPEATS = 5
MIB = 1024 * 1024


def naive_attention(q: torch.Tensor, k: torch.Tensor, v: torch.Tensor, causal: bool = False) -> torch.Tensor:
    """Textbook attention that materializes the full (seq, seq) score matrix.

    q, k, v are all (BATCH, HEADS, SEQ, HEAD_DIM). The return value has the
    same shape. This is the trusted reference, so write it the obvious way.
    """
    # TODO 1: Compute scores = q @ k.transpose(-1, -2) / sqrt(head_dim).
    # The result is (BATCH, HEADS, SEQ, SEQ) — this is the tensor the tiled
    # version exists to avoid.
    #
    # TODO 2: If causal, mask out every position where the key index exceeds
    # the query index. torch.ones(seq, seq, dtype=torch.bool).tril() gives the
    # allowed positions; masked_fill the rest with float("-inf").
    #
    # TODO 3: Numerically stable softmax over the last dimension — subtract
    # scores.amax(dim=-1, keepdim=True), exponentiate, divide by the row sum —
    # then return probs @ v.
    raise NotImplementedError


def tiled_attention(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    kv_tile: int,
    q_tile: int,
    causal: bool = False,
) -> tuple[torch.Tensor, int, int]:
    """Attention computed by streaming over K/V tiles.

    Returns (output, tiles_computed, tiles_skipped). The full (seq, seq) score
    matrix must never exist: the largest score tensor you allocate is one
    (q_tile, kv_tile) block.
    """
    batch, heads, seq, head_dim = q.shape
    out = torch.empty_like(q)
    computed = 0
    skipped = 0

    for q_start in range(0, seq, q_tile):
        q_end = min(q_start + q_tile, seq)
        q_block = q[:, :, q_start:q_end, :]
        rows = q_end - q_start

        # TODO 4: Initialize the three running statistics for this query tile.
        #   running_max:   (batch, heads, rows, 1) filled with float("-inf")
        #   running_denom: (batch, heads, rows, 1) of zeros
        #   accumulator:   (batch, heads, rows, head_dim) of zeros
        # The accumulator stays unnormalized until the tile loop finishes.

        for kv_start in range(0, seq, kv_tile):
            kv_end = min(kv_start + kv_tile, seq)

            # TODO 5: If causal and every key in this tile is strictly in the
            # future of every query row in this query tile
            # (kv_start > q_end - 1), increment `skipped` and `continue`.
            # Otherwise increment `computed`. Skipping is not an optimization
            # detail — it is where causal attention gets its work back.
            computed += 1

            k_block = k[:, :, kv_start:kv_end, :]
            v_block = v[:, :, kv_start:kv_end, :]

            # TODO 6: Compute this tile's scores, shape
            # (batch, heads, rows, kv_end - kv_start), with the same
            # 1/sqrt(head_dim) scaling as the naive path.
            #
            # TODO 7: If causal and the tile straddles the diagonal
            # (kv_end > q_start + 1), build absolute index grids with
            # torch.arange(q_start, q_end).unsqueeze(-1) and
            # torch.arange(kv_start, kv_end).unsqueeze(0), then masked_fill
            # every position where the key index exceeds the query index
            # with float("-inf").
            #
            # TODO 8: Apply the online softmax update.
            #   new_max     = maximum(running_max, scores.amax(-1, keepdim=True))
            #   correction  = exp(running_max - new_max)
            #   probs       = exp(scores - new_max)
            #   running_denom  = running_denom * correction + probs.sum(-1, keepdim=True)
            #   accumulator    = accumulator * correction + probs @ v_block
            #   running_max    = new_max
            # The same `correction` rescales both the denominator and the
            # accumulator. Forgetting it on the accumulator is the classic bug.

        # TODO 9: Normalize once, after the KV loop, and write this query
        # tile's rows into `out`:
        #   out[:, :, q_start:q_end, :] = accumulator / running_denom

    # TODO 10: Delete this raise and return (out, computed, skipped).
    raise NotImplementedError


def score_bytes(batch: int, heads: int, seq: int, tile: int, element_size: int) -> tuple[int, int]:
    """Return (full_score_bytes, one_tile_of_scores_bytes).

    The full score matrix is (batch, heads, seq, seq). One tile of scores,
    covering every query row against one KV tile, is (batch, heads, seq, tile).
    """
    # TODO 11: Compute both from element counts times element_size. Do not
    # hardcode the answer — the sweep below reuses this function at sequence
    # lengths you never run.
    raise NotImplementedError


def report_pair(label: str, a: torch.Tensor, b: torch.Tensor) -> None:
    """Compare two attention outputs.

    The raw max absolute difference is a few float32 ulps and depends on the
    host's BLAS reduction order, so stdout gets a threshold check and stderr
    gets the exact value.
    """
    diff = (a - b).abs().max().item()
    close = torch.allclose(a, b, rtol=RTOL, atol=ATOL)
    print(
        f"  {label:<18s} allclose: {close}   "
        f"max abs diff < {DIFF_THRESHOLD:.0e}: {diff < DIFF_THRESHOLD}"
    )
    print(f"[measured] {label} exact max abs diff: {diff:.3e}", file=sys.stderr)


def time_ms(fn, repeats: int) -> float:
    fn()
    start = time.perf_counter()
    for _ in range(repeats):
        fn()
    return (time.perf_counter() - start) / repeats * 1000.0


def main() -> None:
    torch.manual_seed(0)

    q = torch.randn(BATCH, HEADS, SEQ, HEAD_DIM)
    k = torch.randn(BATCH, HEADS, SEQ, HEAD_DIM)
    v = torch.randn(BATCH, HEADS, SEQ, HEAD_DIM)
    element_size = q.element_size()

    print("=== Online softmax attention on real multi-head tensors ===")
    print(f"Q/K/V shape: {tuple(q.shape)}")
    print(f"dtype: {q.dtype}")
    print(f"softmax scale (1/sqrt(head_dim)): {1.0 / math.sqrt(HEAD_DIM):.5f}")
    print(f"KV tile: {KV_TILE}")
    print(f"KV tiles per query row: {SEQ // KV_TILE}")
    print()

    with torch.inference_mode():
        naive = naive_attention(q, k, v)
        tiled, computed, skipped = tiled_attention(q, k, v, KV_TILE, SEQ)
        sdpa = F.scaled_dot_product_attention(q, k, v)

        print("--- full attention: one query pass, streamed KV tiles ---")
        print(f"output shape: {tuple(tiled.shape)}")
        print(f"output dtype: {tiled.dtype}")
        print(f"KV tiles computed: {computed}")
        print(f"KV tiles skipped: {skipped}")
        report_pair("tiled vs naive", tiled, naive)
        report_pair("tiled vs sdpa", tiled, sdpa)
        report_pair("naive vs sdpa", naive, sdpa)
        print()

        causal_naive = naive_attention(q, k, v, causal=True)
        causal_tiled, causal_computed, causal_skipped = tiled_attention(
            q, k, v, KV_TILE, Q_TILE, causal=True
        )
        causal_sdpa = F.scaled_dot_product_attention(q, k, v, is_causal=True)

        tile_pairs = causal_computed + causal_skipped
        print(f"--- causal attention: query tile {Q_TILE}, KV tile {KV_TILE} ---")
        print(f"tile pairs total: {tile_pairs}")
        print(f"tile pairs computed: {causal_computed}")
        print(f"tile pairs skipped as fully masked: {causal_skipped}")
        print(f"fraction of tile pairs skipped: {causal_skipped / tile_pairs:.4f}")
        report_pair("tiled vs naive", causal_tiled, causal_naive)
        report_pair("tiled vs sdpa", causal_tiled, causal_sdpa)
        report_pair("naive vs sdpa", causal_naive, causal_sdpa)
        print()

    full_bytes, tile_bytes = score_bytes(BATCH, HEADS, SEQ, KV_TILE, element_size)
    print("--- score-matrix memory at this shape ---")
    print(f"element size: {element_size} bytes")
    print(f"full score matrix elements: {BATCH * HEADS * SEQ * SEQ}")
    print(f"full score matrix bytes: {full_bytes}")
    print(f"one KV tile of scores bytes: {tile_bytes}")
    print(f"reduction factor: {full_bytes / tile_bytes:.1f}x")
    print()

    print(f"--- score memory versus sequence length (batch {BATCH}, heads {HEADS}, tile {KV_TILE}) ---")
    for length in MEMORY_SWEEP:
        full, tiled_only = score_bytes(BATCH, HEADS, length, KV_TILE, element_size)
        print(
            f"  L={length:<6d} "
            f"full={full / MIB:>10.1f} MiB  "
            f"tiled={tiled_only / MIB:>7.1f} MiB  "
            f"reduction={full / tiled_only:>7.1f}x"
        )
    print()

    with torch.inference_mode():
        naive_ms = time_ms(lambda: naive_attention(q, k, v), TIMING_REPEATS)
        tiled_ms = time_ms(lambda: tiled_attention(q, k, v, KV_TILE, SEQ), TIMING_REPEATS)
        sdpa_ms = time_ms(lambda: F.scaled_dot_product_attention(q, k, v), TIMING_REPEATS)

    print(f"[measured] naive attention: {naive_ms:.3f} ms", file=sys.stderr)
    print(f"[measured] tiled attention (python loop): {tiled_ms:.3f} ms", file=sys.stderr)
    print(f"[measured] scaled_dot_product_attention: {sdpa_ms:.3f} ms", file=sys.stderr)


if __name__ == "__main__":
    main()
