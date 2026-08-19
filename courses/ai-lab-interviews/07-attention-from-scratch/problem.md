# Attention From Scratch

This is the interview. If you prepare for exactly one implementation, prepare for this one.

You will build causal multi-head self-attention from projections up, then generalize it to grouped-query attention, and verify both against `torch.nn.functional.scaled_dot_product_attention` — the fused kernel that production serving stacks actually call.

## What to implement

1. `split_heads` and `merge_heads` — the reshape/transpose pair that turns $(B, S, d)$ into $(B, H, S, d_h)$ and back.
2. `causal_mask` — the boolean mask, built once and reused.
3. `attention` — scaled dot-product attention with the causal mask, written the explicit way (materializing the score matrix).
4. `repeat_kv` — expand $G$ KV heads to $H$ query heads for GQA.
5. `MultiHeadAttention.forward` — projections, heads, attention, merge, output projection.

## What the script checks

- **Shapes.** Every intermediate tensor has the shape you expect.
- **Correctness against the fused kernel.** Your MHA must match `F.scaled_dot_product_attention(..., is_causal=True)` to float32 tolerance.
- **Causality, tested behaviorally.** The script perturbs a future token and asserts that earlier outputs do not move. This is the check that catches an off-by-one in the mask, which a shape check never will.
- **GQA correctness.** With $G = H$, GQA must reproduce MHA exactly. With $G < H$, it must match a reference built from explicitly repeated KV heads.
- **KV-cache size.** The script reports what the cache costs for a realistic config, so the memory argument for GQA stops being abstract.

## The bar

Fifteen minutes for `attention` and `MultiHeadAttention.forward`, from the empty starter, with autocomplete off, narrating as you go. That is the actual interview bar, and it is reachable with about three repetitions.

## Shape crib

```
x           (B, S, d)
q, k, v     (B, S, d)     -> (B, H, S, dh)      via split_heads
scores      (B, H, S, S)
probs       (B, H, S, S)
out         (B, H, S, dh) -> (B, S, d)          via merge_heads
```

For GQA: `k, v` project to `(B, S, G * dh)` and split into `(B, G, S, dh)`, then repeat to `(B, H, S, dh)`.
