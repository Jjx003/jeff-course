"""
Two-layer MLP with a hand-written backward pass, verified twice.

Everything graded goes to stdout in float64 with a fixed seed, so the numbers
are identical on any machine. Diagnostics go to stderr.

Fill in the four TODO blocks. Do it with autocomplete off and a timer running.
"""

import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

SEED = 0
N, D, H, C = 16, 5, 7, 3
FD_STEP = 1e-5
FD_TOLERANCE = 1e-7
AUTOGRAD_TOLERANCE = 1e-10
TRAIN_STEPS = 20
LEARNING_RATE = 0.5


def init_params(rng):
    """He-style init for the ReLU layer, small init for the output layer."""
    return {
        "W1": rng.normal(0.0, np.sqrt(2.0 / D), size=(D, H)),
        "b1": np.zeros(H),
        "W2": rng.normal(0.0, np.sqrt(1.0 / H), size=(H, C)),
        "b2": np.zeros(C),
    }


def log_softmax(z):
    """Stable log-softmax over the last axis."""
    shifted = z - z.max(axis=-1, keepdims=True)
    return shifted - np.log(np.exp(shifted).sum(axis=-1, keepdims=True))


def forward(params, x, y):
    """Return (loss, cache). y holds integer class labels.

    TODO 1: implement the forward pass.
      z1 = x @ W1 + b1                       (N, H)
      h1 = relu(z1)                          (N, H)
      z2 = h1 @ W2 + b2                      (N, C)
      loss = mean over the batch of -log_softmax(z2)[i, y[i]]

    Put into the cache everything backward will need: x, y, z1, h1, and the
    softmax probabilities. Caching probs rather than logits keeps backward
    free of any second exponentiation.
    """
    raise NotImplementedError


def backward(params, cache):
    """Hand-written gradients for every parameter.

    TODO 2: return {"W1": ..., "b1": ..., "W2": ..., "b2": ...}.

      dz2 = (probs - onehot(y)) / N          (N, C)  <- the 1/N lives here
      dW2 = h1.T @ dz2                       (H, C)
      db2 = dz2.sum(axis=0)                  (C,)
      dh1 = dz2 @ W2.T                       (N, H)
      dz1 = dh1 * (z1 > 0)                   (N, H)  <- a mask, not a matmul
      dW1 = x.T @ dz1                        (D, H)
      db1 = dz1.sum(axis=0)                  (H,)

    Every shape above is forced: a gradient has the same shape as its tensor,
    so there is exactly one way to arrange each product.
    """
    raise NotImplementedError


def numerical_gradient(params, x, y, name, step=FD_STEP):
    """Central finite differences for one parameter tensor.

    TODO 3: for every scalar entry of params[name], evaluate the loss at
    +step and -step and set the gradient entry to
    (loss_plus - loss_minus) / (2 * step). Restore the original value before
    moving on, or later entries are computed against a perturbed model.

    Reshaping the parameter to 1-D gives you a view over the same memory, so
    writing through the flat view mutates the real parameter and lets one loop
    handle both matrices and vectors.
    """
    raise NotImplementedError


def relative_error(a, b, eps=1e-12):
    """Scale-aware comparison, so big and small gradients are judged fairly.

    TODO 4: return max(|a - b| / max(|a| + |b|, eps)) over all entries.
    """
    raise NotImplementedError


def torch_reference(params, x, y):
    """Same model in torch. nn.Linear stores weights transposed."""
    model = nn.Sequential(
        nn.Linear(D, H),
        nn.ReLU(),
        nn.Linear(H, C),
    ).double()
    with torch.no_grad():
        model[0].weight.copy_(torch.from_numpy(params["W1"].T))
        model[0].bias.copy_(torch.from_numpy(params["b1"]))
        model[2].weight.copy_(torch.from_numpy(params["W2"].T))
        model[2].bias.copy_(torch.from_numpy(params["b2"]))

    xt = torch.from_numpy(x)
    yt = torch.from_numpy(y)
    loss = F.cross_entropy(model(xt), yt)
    loss.backward()

    return float(loss.item()), {
        "W1": model[0].weight.grad.numpy().T,
        "b1": model[0].bias.grad.numpy(),
        "W2": model[2].weight.grad.numpy().T,
        "b2": model[2].bias.grad.numpy(),
    }


def make_batch(rng):
    """A separable toy problem: class centroids plus noise."""
    y = rng.integers(0, C, size=N)
    centroids = rng.normal(0.0, 1.5, size=(C, D))
    x = centroids[y] + rng.normal(0.0, 0.35, size=(N, D))
    return x, y


def main():
    np.set_printoptions(precision=6, suppress=True)
    rng = np.random.default_rng(SEED)
    torch.manual_seed(SEED)

    params = init_params(rng)
    x, y = make_batch(rng)

    print("=== Two-layer MLP, hand-written backward ===")
    print(f"batch: N={N} D={D} H={H} C={C}   dtype: {x.dtype}")

    loss, cache = forward(params, x, y)
    grads = backward(params, cache)
    print(f"initial loss: {loss:.6f}")
    print(f"chance loss (ln C): {np.log(C):.6f}")

    print()
    print("--- check 1: central finite differences ---")
    print(f"step h = {FD_STEP:g}, tolerance = {FD_TOLERANCE:g}")
    fd_ok = True
    for name in ("W1", "b1", "W2", "b2"):
        numeric = numerical_gradient(params, x, y, name)
        err = relative_error(grads[name], numeric)
        ok = err < FD_TOLERANCE
        fd_ok = fd_ok and ok
        print(f"  {name:<3} shape {str(grads[name].shape):<8} rel err < 1e-07: {ok}")
        print(f"      analytic vs numeric: {err:.3e}", file=sys.stderr)
    print(f"finite differences agree: {fd_ok}")

    print()
    print("--- check 2: torch autograd ---")
    torch_loss, torch_grads = torch_reference(params, x, y)
    print(f"loss matches torch: {abs(torch_loss - loss) < AUTOGRAD_TOLERANCE}")
    ag_ok = True
    for name in ("W1", "b1", "W2", "b2"):
        err = relative_error(grads[name], torch_grads[name])
        ok = err < AUTOGRAD_TOLERANCE
        ag_ok = ag_ok and ok
        print(f"  {name:<3} matches autograd: {ok}")
        print(f"      analytic vs autograd: {err:.3e}", file=sys.stderr)
    print(f"autograd agrees: {ag_ok}")

    print()
    print("--- check 3: it actually trains ---")
    train_params = {k: v.copy() for k, v in params.items()}
    losses = []
    for _ in range(TRAIN_STEPS):
        step_loss, step_cache = forward(train_params, x, y)
        step_grads = backward(train_params, step_cache)
        losses.append(step_loss)
        for name in train_params:
            train_params[name] -= LEARNING_RATE * step_grads[name]

    final_loss, _ = forward(train_params, x, y)
    monotone = all(b < a for a, b in zip(losses, losses[1:] + [final_loss]))
    print(f"steps: {TRAIN_STEPS}   lr: {LEARNING_RATE}")
    print(f"loss start -> end: {losses[0]:.6f} -> {final_loss:.6f}")
    print(f"loss decreased every step: {monotone}")
    print(f"final loss below 0.1: {final_loss < 0.1}")

    print()
    print(f"ALL CHECKS PASS: {fd_ok and ag_ok and monotone}")


if __name__ == "__main__":
    main()
