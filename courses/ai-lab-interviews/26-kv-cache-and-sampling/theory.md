# The Cache

## What is stored

Keys and values for every position, per layer. Note that with GQA the cache holds $G$ heads, not $H$ — the `repeat_interleave` to $H$ heads happens *after* the cache read, never before. Storing repeated heads would throw away the entire benefit of GQA, and it is a real bug that people ship.

```python
if past_k is not None:
    k = torch.cat([past_k, k], dim=2)   # concatenate along sequence
    v = torch.cat([past_v, v], dim=2)
new_cache = (k, v)
```

Concatenating along `dim=2` — the sequence axis of a `(B, H, S, d_h)` tensor. A production implementation preallocates to the maximum length and writes into a slice instead, because `cat` reallocates every step; but the semantics are the same and `cat` is clearer for an interview.

## The offset

```python
q = apply_rope(q, cos, sin, offset)
k = apply_rope(k, cos, sin, offset)
```

with `offset` = the number of tokens already in the cache. During prefill it is 0 and the query spans positions $0..S-1$. During decoding it is the length so far, and the single query token sits at exactly that absolute position.

Say this out loud when you implement it. It is the detail an interviewer is waiting for.

## The mask

During prefill, query length equals key length and you need the usual causal mask.

During decode, query length is 1 and key length is $t+1$. Position $t$ may attend to everything cached — that is the *point* of the cache — so no mask is required.

The general form, for a query block of length $s$ at the end of a key sequence of length $T$:

```python
mask = torch.ones(s, T, dtype=torch.bool).tril(diagonal=T - s)
```

The `diagonal=T - s` shifts the triangle so it aligns to the *right* edge. With $s = T$ this reduces to a plain `tril`; with $s = 1$ it is all ones. That single expression handles prefill, decode, and chunked prefill, and being able to write it is a good signal.

## The complexity change

| | Per step | Total for $n$ tokens |
|---|---|---|
| Uncached | $O(t^2)$ attention + $O(t)$ FFN over the whole prefix | $O(n^3)$ |
| Cached | $O(t)$ attention + $O(1)$ FFN | $O(n^2)$ |

At the small sizes in this exercise the wall-clock difference is modest, because Python and kernel-launch overhead dominate. At production sizes it is the difference between working and not.

# Sampling

## Order of operations

Penalties, then temperature, then truncation, then renormalize.

The reason truncation comes after temperature: temperature changes the *shape* of the distribution, so a top-p cutoff computed before it would be measuring a distribution you are not going to sample from. Doing it in the wrong order gives behavior that is hard to debug because it is subtly wrong rather than obviously broken.

## Temperature

$$p_i = \frac{e^{z_i/T}}{\sum_j e^{z_j/T}}$$

$T<1$ concentrates mass on the top tokens; $T>1$ spreads it. $T\to0$ approaches greedy, and $T=0$ needs a special case because you cannot divide by zero.

Note temperature **never changes the argmax** — it is a monotone transformation of the logits. That is a nice property to state, and it explains why temperature alone cannot fix a model that is confidently wrong.

## Top-k

Keep the $k$ largest logits, mask the rest to $-\infty$, renormalize.

```python
threshold = logits.topk(k, dim=-1).values[..., -1:]
logits = logits.masked_fill(logits < threshold, float("-inf"))
```

Using `<` rather than `<=` keeps ties, so you may retain slightly more than $k$ tokens on an exact tie. That is the right behavior — arbitrarily breaking a tie by index is worse.

## Top-p (nucleus)

Keep the smallest set of tokens whose cumulative probability reaches $p$.

```python
sorted_logits, sorted_idx = logits.sort(dim=-1, descending=True)
probs = sorted_logits.softmax(dim=-1)
cumulative = probs.cumsum(dim=-1)

remove = cumulative - probs >= p      # shifted: "the mass BEFORE this token"
remove[..., 0] = False                # always keep the top token
to_remove = remove.scatter(-1, sorted_idx, remove)
logits = logits.masked_fill(to_remove, float("-inf"))
```

Two details that are easy to get wrong and that the script checks:

- **The shift.** Comparing `cumulative >= p` would drop the token that *crosses* the threshold, so the retained mass would be strictly less than $p$. Subtracting the token's own probability compares the mass *before* it, which keeps the crossing token — that is what "smallest set whose cumulative probability reaches $p$" means.
- **Always keep the top token.** If one token already has probability above $p$, the naive condition removes everything and the softmax over an all-`-inf` row is `nan`. Forcing index 0 to survive is the standard guard.

## Why top-p over top-k

The script demonstrates it directly. Given a confident distribution and an uncertain one:

- Top-p 0.9 keeps **1** token from the confident distribution and **5** from the uncertain one.
- Top-k with any fixed $k$ keeps $k$ from both.

A fixed $k$ is too permissive when the model is confident — admitting nonsense into a step that was nearly deterministic — and too restrictive when it is uncertain. Nucleus sampling adapts. That is the whole argument, and it is much more convincing with the numbers attached.
