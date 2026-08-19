# Walkthrough

## split_heads and merge_heads

```python
x.view(b, s, n_heads, head_dim).transpose(1, 2)
x.transpose(1, 2).contiguous().view(b, s, h * head_dim)
```

Two things to say out loud when you write these.

**The view splits the feature axis, not the sequence axis.** The projection laid heads out contiguously along `d`, so head `h` owns channels `[h*dh, (h+1)*dh)`. Viewing as `(B, n_heads, S, head_dim)` would carve up the sequence instead — the shape is right, the semantics are garbage, and nothing downstream will complain.

**`.contiguous()` on the way back.** `transpose` returns a view with permuted strides. `view` needs contiguous memory and raises. `reshape` would silently copy for you; using it is fine, but knowing why is what the question is about.

## causal_mask

`torch.ones(seq, seq, dtype=torch.bool).tril()` — lower triangle, diagonal included, so query `i` sees keys `0..i` and itself. `tril(diagonal=-1)` would hide the current token, giving a model that cannot see its own position.

Building it as `(S, S)` lets it broadcast across `(B, H, S, S)` for free. In a real model this is a non-persistent buffer, built once.

## repeat_kv

`repeat_interleave(n_rep, dim=1)`. The failure mode is `repeat`, which produces the same shape with the wrong head ordering: query heads are grouped contiguously, so KV head 0 must serve query heads `0..n_rep-1`, which is exactly what interleaving gives.

The memory-efficient production form is `x[:, :, None].expand(b, g, n_rep, s, dh).reshape(b, g * n_rep, s, dh)`, which avoids materializing a copy when the consumer can take a broadcast view.

## attention

```python
scores = q @ k.transpose(-2, -1) / math.sqrt(head_dim)
scores = scores.masked_fill(~mask, float("-inf"))
probs  = scores.softmax(dim=-1)
return probs @ v
```

`k.transpose(-2, -1)` and not `k.T` — on a 4-D tensor `.T` reverses every dimension.

The `1/sqrt(head_dim)` is variance control: a dot product of two unit-variance vectors of length `d_h` has standard deviation `sqrt(d_h)`, so without the division softmax saturates as head dimension grows, and a saturated softmax has vanishing gradient.

`float("-inf")` rather than a large negative constant. Softmax subtracts the row max before exponentiating, so `-inf` becomes exactly zero probability. A finite sentinel like `-1e9` also gives exactly zero in fp32 and bf16 — the exponent underflows — but it overflows on a cast to fp16 (max 65504), and any pipeline that adds a second bias or mask after it can pull it back into range. `-inf` is unambiguous under all of that.

## forward

```python
q = split_heads(self.wq(x), self.n_heads)
k = split_heads(self.wk(x), self.n_kv_heads)
v = split_heads(self.wv(x), self.n_kv_heads)
k, v = repeat_kv(k, self.n_rep), repeat_kv(v, self.n_rep)
return self.wo(merge_heads(attention(q, k, v, causal_mask(seq, x.device))))
```

The asymmetry — `q` into `n_heads`, `k` and `v` into `n_kv_heads` — is the entirety of GQA. Everything else is unchanged, which is exactly why GQA was adopted so quickly.

## Why the causality test is the important one

The script perturbs the input at position `t` by a large amount and asserts every output before `t` is bit-identical. A shape assertion cannot catch `triu` where you meant `tril`, or a mask off by one, or masking after the softmax. This test catches all three.

The reason it matters so much: a leaky causal mask makes training loss look *better*, because the model is reading the answer. You only find out at generation time, when the model is incoherent, after burning the compute.

## Tolerances

`1e-5` against the fused kernel: `F.scaled_dot_product_attention` accumulates in a different order, so float32 differences around `1e-7` are expected and mean nothing.

`1e-6` for causality and for the `G == H` equivalence: those must be exact, because they compare identical computations.

## The follow-ups

- **"Add a KV cache."** Store `past_k`, `past_v`; concatenate along the sequence axis; during decoding the query length is 1, so the causal mask is unnecessary — position `t` legitimately attends to all of `0..t`.
- **"Why is decoding memory-bound?"** Per generated token you read the whole cache from HBM and do only a rank-1 update worth of compute. Arithmetic intensity is roughly 1 FLOP per byte, far below what the hardware needs to saturate its FLOPs.
- **"Where does FlashAttention help?"** It never materializes the `(B, H, S, S)` score tensor, tiling the computation with an online softmax recurrence instead. Compute is unchanged; the memory footprint drops from `O(S^2)` to `O(S)`, and HBM traffic falls by roughly the SRAM-to-head-dimension ratio rather than becoming linear.
