# Backprop From Scratch

This is the numpy interview. It shows up when the interviewer wants to know whether you understand gradients or merely understand `loss.backward()`.

You will implement a two-layer MLP — linear, ReLU, linear, softmax cross-entropy — with a hand-written backward pass, and then prove it correct twice: once against central finite differences, and once against PyTorch autograd on identical inputs.

## What to implement

Fill in the `TODO` blocks in the starter. In order:

1. `forward` — the full forward pass, returning the loss and a cache of everything backward will need.
2. `backward` — gradients for `W1`, `b1`, `W2`, `b2`, computed by hand.
3. `numerical_gradient` — a central finite difference estimator.
4. `relative_error` — the comparison metric, so a big gradient and a small one are judged fairly.

The script then runs three checks and prints a deterministic report:

- **Finite differences.** Every parameter's analytic gradient must match its numerical estimate to a relative error below `1e-7` in float64.
- **Autograd.** The same model built with `torch.nn` must produce identical gradients.
- **Training.** Twenty steps of plain SGD on a separable toy problem must drive the loss down monotonically, because a wrong gradient can still pass a sloppy check but will not train.

## Rules of engagement

Autocomplete off. Give yourself 35 minutes for the two gradient functions before you look at anything. In the real interview you will not have this starter — you will have an empty file and someone watching.

## Hints on shapes

The batch is `(N, D)`. The hidden layer is `(N, H)`. The logits are `(N, C)`.

- `dlogits` is `(N, C)` and equals `(probs - onehot) / N`. The `/ N` is because the loss is a mean.
- `dW2` is `(H, C)`. There is exactly one way to contract `h` and `dlogits` to get that shape.
- The ReLU backward is a mask, not a matmul.
- `db1` and `db2` sum away the batch dimension.
