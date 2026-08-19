# Assembling the Model

## The block

```python
def forward(self, x, cos, sin):
    x = x + self.attn(self.norm1(x), cos, sin)
    x = x + self.ffn(self.norm2(x))
    return x
```

Two things must be exactly right.

**The residual adds the *unnormalized* `x`.** `x + sublayer(norm(x))`, never `norm(x) + sublayer(norm(x))`. The whole benefit of pre-norm is that the residual stream is an unobstructed additive path from input to output; normalizing what flows into the addition destroys it.

**Each sublayer gets its own norm.** Reusing one norm module for both positions ties their learned scales together. It trains — slightly worse — and is nearly invisible, which is what makes it a good seeded bug.

## The model

```python
def forward(self, ids):
    x = self.embed(ids)
    for block in self.blocks:
        x = block(x, self.cos, self.sin)
    x = self.norm_f(x)              # mandatory in pre-norm
    return x @ self.embed.weight.T  # tied head
```

**The final norm is not optional.** The residual stream's magnitude grows with depth in a pre-norm model, so without a final normalization the logits are scaled by an arbitrary depth-dependent factor. Everything still trains; quality is quietly worse. Omitting it is the single most common seeded bug in a debug-the-transformer interview.

**Weight tying** as `x @ self.embed.weight.T`. Because it is the same tensor, the gradient it receives is the sum of the embedding-lookup path and the output-projection path — the branch-sum rule showing up in production code.

## The shift

Next-token prediction means position $t$ predicts token $t+1$. There are two equivalent conventions and mixing them is a real bug:

```python
# Convention A: shift inside the loss
logits = model(ids)                      # (B, S, V)
loss = F.cross_entropy(
    logits[:, :-1].reshape(-1, V),
    ids[:, 1:].reshape(-1),
)

# Convention B: shift in the data loader
x, y = tokens[:-1], tokens[1:]
loss = F.cross_entropy(model(x).reshape(-1, V), y.reshape(-1))
```

**Do not do both.** A double shift makes the model predict two tokens ahead; loss plateaus around 3–4 and generation is subtly wrong forever.

Note also that `F.cross_entropy` does *not* shift anything for you. That is a persistent myth, and it is worth being sure about because an interviewer may float it to see whether you know.

## The initialization check

| Vocabulary | $\ln V$ |
|---|---|
| 32,000 | 10.37 |
| 50,257 | 10.82 |
| 128,000 | 11.76 |
| 256,000 | 12.45 |

At step 0 the model is uninformative, so its best output is uniform and its cross-entropy is $\ln V$.

Diagnosing from the deviation:

- **Much higher** — the output projection is initialized too large, or the final norm is missing so the logits carry a large scale.
- **Much lower** — the model is seeing the answer. Broken causal mask, a double shift, or labels equal to inputs.
- **Exactly $\ln V$ but never moves** — the gradient is not reaching the parameters. A `detach` in the wrong place, a `no_grad` block, or parameters missing from the optimizer.

## Overfitting one batch

The second-fastest diagnostic. Take one batch, turn off dropout and weight decay, and train until the loss is essentially zero. A correct model memorizes a small sequence within a few hundred steps.

If it cannot, the bug is in the model or the optimizer, not the data. This eliminates half the search space in about a minute of compute, and saying so unprompted in an interview is a strong signal — it is what a person who has actually debugged training runs does first.

## Initialization

Modern LMs use a normal initialization with $\sigma = 0.02$, plus one refinement worth knowing: the projections that write *into* the residual stream — the attention output and the FFN down projection — are scaled by $1/\sqrt{2L}$.

The reason is variance accumulation. Each of $2L$ sublayers adds its output into the residual stream. Without the correction, the stream's variance grows linearly in depth, so deep models start with badly scaled activations. GPT-2 introduced this and essentially everything since has kept it.
