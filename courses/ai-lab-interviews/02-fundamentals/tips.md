# Answers Worth Having Verbatim

**"Write the backward pass for a linear layer."**
> `dX = dZ @ W.T`, `dW = X.T @ dZ`, `db = dZ.sum(0)`. Shapes fall out of Rule 1 — every gradient matches its tensor. `W` and `b` are shared across the batch so their gradients sum over it; `X` is per-example so the batch dimension survives.

**"What is the gradient of cross-entropy with respect to the logits?"**
> `p - onehot(t)`. That is why frameworks fuse softmax and cross-entropy and why `F.cross_entropy` takes logits, not probabilities.

**"Why SwiGLU?"**
> Gating gives the FFN a multiplicative interaction that a plain ReLU MLP cannot express, and it empirically wins at fixed compute. It costs a third weight matrix, so the hidden dimension is shrunk to about `8d/3` to hold parameters constant.

**"How would you verify a hand-written backward pass?"**
> Central finite differences in float64, `h` around `1e-5`, compared by relative error. Then cross-check against autograd on the same inputs.

**"What is gradient checkpointing?"**
> Recompute activations in the backward pass instead of storing them. With `sqrt(N)` checkpoints, memory drops from `O(N)` to `O(sqrt(N))` for roughly a 33% increase in training compute.

# Traps

- Passing probabilities to `F.cross_entropy`. It wants logits.
- Forgetting `optimizer.zero_grad()`. Gradients accumulate by design.
- Saying "backward is the same cost as forward". Same big-O; roughly 2x the FLOPs.
- Claiming ReLU has no derivative at zero and stopping there. It is subdifferentiable; frameworks pick 0 and it does not matter in practice. Say the second half.
- Forgetting that gradients sum at branch points. This is where weight-tied embeddings bite.

# Further Reading

- [CS231n: Backpropagation](https://cs231n.github.io/optimization-2/) — still the clearest treatment of the computation-graph view.
- [CS224n: Self-Attention and Transformers](https://web.stanford.edu/class/cs224n/) — the notes bridge this material into the next unit.
- [Yes you should understand backprop](https://karpathy.medium.com/yes-you-should-understand-backprop-562f4b1e1eda) — Karpathy on why abstracting this away costs you.
