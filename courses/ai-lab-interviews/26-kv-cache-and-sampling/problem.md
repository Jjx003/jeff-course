# KV Cache and Sampling

Two of the most-asked inference implementations, in one module. "Now add a KV cache" is the standard follow-up to an attention question, and "implement top-p sampling" is a standalone prompt in its own right.

## What to implement

1. `Attention.forward` with cache support — concatenate past keys and values, and apply RoPE at the **correct absolute offset**.
2. `generate_cached` — prefill once, then feed one token at a time.
3. `apply_temperature`, `top_k_filter`, `top_p_filter`, `sample`.

## The invariant that defines correctness

> **Cached generation must produce exactly the same tokens as uncached generation.**

Not similar. Identical. The script generates 48 tokens both ways and compares them token for token. Everything else a KV cache does is an optimization on top of that guarantee, and if the guarantee is broken the optimization is worthless.

## The bug this module is really about

RoPE encodes **absolute** position. During prefill, token $i$ sits at position $i$ and everything is fine. During decoding you feed a tensor of shape `(B, 1, d)`, so its internal index is 0 — and if you rotate it by position 0, every generated token believes it is the first token in the sequence.

The model still runs. The shapes are right. Generation produces fluent-looking text. It is simply wrong, and it degrades as the sequence gets longer.

The script isolates this: it runs the same token through the same cache at offset 0 and at offset 16 and reports the gap in the logits. Seeing that number is worth more than being told about the bug.

## The mask subtlety

With a cache and a single query token, position $t$ may legitimately attend to all of $0..t$ — so **no causal mask is needed during decoding**. A mask is only required when the query length exceeds 1, and then it must be aligned to the *end* of the key sequence, not the start. Getting this wrong is the second-most-common KV-cache bug.
