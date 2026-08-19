# The Six Bugs

## 1. `causal_mask` uses `triu` instead of `tril`

```python
return torch.ones(seq, seq, dtype=torch.bool, device=device).triu()   # bug
return torch.ones(seq, seq, dtype=torch.bool, device=device).tril()   # fix
```

The mask is inverted: every token attends only to the *future*, and token 0 attends to everything. Training loss collapses because the answer is visible, and generation is meaningless because at inference there is no future to read.

Detected by probe 1, whose row-sum check is the sharper of the two — `[1, 2, ..., n]` is a fingerprint no other triangle produces.

## 2. `split_heads` carves the sequence axis

```python
return x.view(b, n_heads, s, head_dim)                       # bug
return x.view(b, s, n_heads, head_dim).transpose(1, 2)       # fix
```

Both produce `(B, H, S, dh)`. The buggy version reinterprets the flat buffer so that "head 0" is the first `S/H` tokens rather than the first `dh` feature channels — heads become sequence chunks, and the round trip through `merge_heads` no longer returns the original tensor.

This is the most instructive bug in the file. Nothing about the shapes, the loss, or the gradients complains. The model still trains, to a mediocre plateau.

Detected by probe 2's round-trip and channel-slice checks.

## 3. Missing `1/sqrt(head_dim)`

```python
scores = q @ k.transpose(-2, -1)                       # bug
scores = q @ k.transpose(-2, -1) / math.sqrt(head_dim) # fix
```

At `head_dim = 8` this is a factor of 2.83 on the logits — survivable. At `head_dim = 128` it is 11.3, softmax saturates, gradients vanish, and training stalls or diverges. The bug scales with the model, which is exactly the worst property a bug can have.

Detected by probe 3, which compares against the fused kernel with an open mask so the comparison isolates the scalar.

## 4. RoPE applied to V

```python
v = apply_rope(v, cos, sin)   # bug: delete this line
```

Position should determine *which* tokens you attend to, not *what* is retrieved from them. Rotating V means the retrieved content is a position-dependent rotation of the value vector, which the model then has to spend capacity undoing.

Detected by probe 4, which compares the whole attention module to a reference that rotates Q and K only.

## 5. The final norm is never applied

```python
return x                # bug
return self.norm_f(x)   # fix
```

`self.norm_f` is constructed in `__init__` and never called. In a pre-norm architecture the residual stream's magnitude grows with depth, so the logits carry an arbitrary depth-dependent scale.

Detected by probe 5, which measures the RMS of the hidden state entering the output head. Note that probe 7 — the `ln V` check — **passes** despite this bug, because this model is only four layers deep with a small initialization. That is worth knowing: the `ln V` check is a good coarse filter, not a fine one, and at production depth this bug would move it substantially.

## 6. The loss is not shifted

```python
return F.cross_entropy(logits.reshape(-1, vocab), ids.reshape(-1))                             # bug
return F.cross_entropy(logits[:, :-1, :].reshape(-1, vocab), ids[:, 1:].reshape(-1))           # fix
```

Position `t` is trained to predict token `t` rather than token `t+1`. The task becomes copy-the-input, which is trivial: the model routes the current embedding straight to the output and the loss collapses to nearly zero.

Detected by probe 6, which uses **no model at all** — hand-built oracle logits for the next token should give loss ≈ 0, and oracle logits for the current token should give a large loss. Building probes for a loss function in isolation is a habit worth having.

# The Lesson About Probe 9

With bug 6 in place, the end-to-end memorization check reports:

```
loss 6.2123 -> 0.0000 over 300 steps
[PASS] final loss below 0.05
```

The loss is not just low, it is *lower than the correct implementation reaches*. And greedy decoding produces garbage.

This is the whole point of the module. A loss that falls means something is learnable, not that the right thing is being learned. Pair every loss check with a behavioral one — generation, causality, held-out evaluation. In an interview, saying this out loud when you notice it is worth more than any individual fix.

# Debugging Order in Practice

If you had no probe harness, the order to work in would be:

1. **Read `__init__` against `forward`.** Anything constructed and never called is free to find.
2. **Test the loss with oracle logits.** No model needed, and it eliminates a whole class of bug in thirty seconds.
3. **Check invariants on pure functions.** Masks, reshapes, rotations all have properties you can assert in one line.
4. **Compare each kernel to a torch primitive.** `scaled_dot_product_attention` is a free oracle.
5. **Check `ln V` at init.** Coarse, but nearly free.
6. **Check causality behaviorally.** Perturb the future, watch the past.
7. **Only then** train anything.
