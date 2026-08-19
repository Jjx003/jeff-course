# The Five Lines That Matter

Everything else in this module is scaffolding around these:

```python
scores = q @ k.transpose(-2, -1) / math.sqrt(head_dim)   # (B, H, S, S)
scores = scores.masked_fill(~mask, float("-inf"))
probs  = scores.softmax(dim=-1)
out    = probs @ v                                        # (B, H, S, dh)
```

## The head reshape, in detail

This is where most people lose time in an interview, so it is worth having the exact incantation cached.

```python
# (B, S, d) -> (B, S, H, dh) -> (B, H, S, dh)
q = q.view(B, S, H, head_dim).transpose(1, 2)
```

Two separate operations, and each is load-bearing:

- **`view(B, S, H, head_dim)`** splits the last axis. This works because the projection laid out the heads contiguously along `d` — head `h` owns channels `[h*dh, (h+1)*dh)`. If you instead did `view(B, H, S, head_dim)` you would be slicing along the *sequence* axis and mixing tokens into heads. That is a silent, plausible-looking bug that trains to garbage.
- **`transpose(1, 2)`** moves heads ahead of sequence, so the subsequent matmul batches over `(B, H)` and operates on `(S, dh)` matrices.

Coming back:

```python
# (B, H, S, dh) -> (B, S, H, dh) -> (B, S, d)
out = out.transpose(1, 2).contiguous().view(B, S, d)
```

The `.contiguous()` is required. `transpose` produces a non-contiguous view — it only permutes strides — and `view` demands contiguous memory. You can use `.reshape()` instead, which copies when it must, but knowing *why* is what the question is really about.

## Building the mask

```python
mask = torch.ones(S, S, dtype=torch.bool, device=device).tril()
```

`tril` keeps the lower triangle including the diagonal, which is what you want: query $i$ may attend to keys $0..i$, itself included. `tril(diagonal=-1)` would exclude the current token, and a model that cannot see its own position is a subtly different and much worse model.

Broadcasting: the mask is $(S, S)$ and the scores are $(B, H, S, S)$, so it broadcasts across batch and heads for free. Register it as a buffer rather than rebuilding it per forward pass; in real implementations it is `register_buffer(..., persistent=False)` so it does not bloat the checkpoint.

## Testing causality properly

A shape test cannot catch a mask that is off by one. A behavioral test can:

> Change the input at position $t$. Every output at positions $< t$ must be bit-identical.

If output $t-1$ moves when input $t$ changes, information flowed backward in time. In an autoregressive LM that is catastrophic and nearly invisible: training loss drops beautifully, because the model is peeking at the answer, and generation is incoherent. This is the single most valuable test in the module and the thing to mention unprompted in an interview.

## GQA implementation

Project K and V to $G$ heads instead of $H$, then expand before the score matmul:

```python
# k: (B, G, S, dh) -> (B, H, S, dh)
k = k.repeat_interleave(n_rep, dim=1)
```

`repeat_interleave` and not `repeat`. The distinction matters: with $H=8, G=2$, `repeat_interleave(4)` gives head order `[0,0,0,0,1,1,1,1]` while `repeat` gives `[0,1,0,1,0,1,0,1]`. Both produce correct-looking shapes. Only one matches the grouping the weights were trained with, and it is the interleaved one — query heads are grouped contiguously.

For a memory-efficient version, `expand` on a new axis followed by `reshape` avoids materializing the copy where the kernel can consume a broadcast view. Production implementations use that form.

## What the KV cache costs

![Two panels. Left: KV cache per sequence against context length for MHA, GQA and MQA on Llama-2-70B geometry, all straight lines on a log-log plot. Right: total KV cache against number of concurrent sequences at 4k context, crossing available HBM well before batch 64 for MHA.](/courses/ai-lab-interviews/kv-cache-growth.svg)

Per token, per layer:

$$\text{bytes} = 2 \times G \times d_h \times \text{dtype bytes}$$

The 2 is for K and V. For a 32-layer model with $d_h = 128$ in bf16:

| Attention | $G$ | Bytes/token/layer | 4096 tokens, 32 layers |
|---|---|---|---|
| MHA, $H=32$ | 32 | 16,384 | 2.1 GB |
| GQA, $G=8$ | 8 | 4,096 | 0.54 GB |
| MQA | 1 | 512 | 0.07 GB |

At batch 64, MHA needs 134 GB of cache — more than an H100 has, before the weights. GQA brings it to 34 GB. That single table is the entire argument for GQA, and it is the kind of number that makes a technical discussion go well.
