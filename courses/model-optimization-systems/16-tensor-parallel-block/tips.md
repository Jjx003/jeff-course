# Hints

## Getting the axes right

- Weights follow the nn.Linear convention `(out_features, in_features)` and
  are applied as `x @ W.T`. Column parallel = split output features =
  `torch.chunk(w, tp, dim=0)`. Row parallel = split input features = `dim=1`.
- If `reassembled == original` prints `False`, you concatenated along the
  wrong axis — `torch.cat` must invert your `torch.chunk` exactly.
- `torch.chunk` returns views; that is fine here. No copies are needed.

## The MLP

- The local activation after the column shard has shape `(B, S, FFN // tp)`.
  If you see `(B, S, FFN)` per rank, you sharded nothing.
- Exactly one `ledger.all_reduce` call. Summing partials yourself with `sum()`
  and then calling the ledger anyway double-counts — the assertion on
  `block_ledger.calls == 2` will catch it.

## Attention

- Shard the *projection weights* by heads: with 8 query heads, 4 KV heads,
  head dim 32 and TP 4, each rank's `w_q` shard is `(64, 256)` and its
  `w_k`/`w_v` shards are `(32, 256)`.
- Call `split_heads` with the *per-rank* head counts (`Q_HEADS // tp`,
  `KV_HEADS // tp`), not the global ones. The GQA broadcast inside
  `attention` then works unchanged because 2 local query heads / 1 local KV
  head has the same group size as 8/4.
- The output projection consumes local heads only: each rank's `w_o` row
  shard is `(256, 64)` and its result is a partial sum over ranks, exactly
  like the MLP's second matmul.

## The wrong cut

- Split `x` with `torch.chunk(x, tp, dim=-1)` and pair each slice with the
  matching row shard of `w_up`. Apply the activation to each partial, then
  sum. Do not "fix" it — the point is to measure the damage.
- Sanity check: if you accidentally all-reduce before the activation, the
  relative error collapses to rounding level and the final
  `assert rel_err > 0.1` fails. That assertion failing means you implemented
  the *right* cut in the wrong function.

## The cost table

- `mem_ms = total_weight_bytes / (tp * HBM_PER_GPU) * 1e3` — the shard read
  happens on all GPUs in parallel.
- Guard the `tp == 1` row: no collectives, and it sets `base`.
- Expected corners: `41.79` ms at TP 1, `6.82` ms and `6.12x` at TP 8.

## If fp32 allclose fails but the integer certificate passes

That combination is nearly impossible for a correct implementation — it means
your fp32 path and integer path take different code routes. Make sure both go
through the same `tp_mlp` with only the activation function swapped.
