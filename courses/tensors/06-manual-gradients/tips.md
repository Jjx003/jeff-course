# Tips & Notes

## Draw the Computation Graph First

Before writing any code, sketch the forward pass:

```
X  ──┐
     ├─ matmul ─→ Z ─→ add b ─→ y_pred ─→ MSE ─→ loss
W  ──┘                  ↑
                        b
```

Then work **right to left** when deriving gradients. Each node only needs to
know: "given the gradient of the loss with respect to my output, what is the
gradient with respect to each of my inputs?"

## Shape Bookkeeping

Shapes are your best debugging tool. The gradient of a scalar loss with
respect to a variable must have the **same shape** as that variable:

| Variable | Shape | Gradient shape |
|----------|-------|----------------|
| `W` | `(D, 1)` | `(D, 1)` |
| `b` | `(1,)` | scalar or `(1,)` |
| `X` | `(N, D)` | `(N, D)` |
| `y_pred` | `(N, 1)` | `(N, 1)` |

If a gradient has the wrong shape, your matrix multiply has the wrong operand
order. Try transposing one side.

## Deriving dL/dW by Shape

You know:
- Upstream gradient `delta` has shape `(N, 1)`
- `W` has shape `(D, 1)`
- `dL_dW` must have shape `(D, 1)`

The only product of `X` (shape `(N, D)`) and `delta` (shape `(N, 1)`) that
produces `(D, 1)` is `X.T @ delta`. This shape argument alone tells you the
correct formula.

## Common Pitfalls

- **Forgetting the 2/N factor**: the gradient of MSE is $(2/N)(y\_pred - y)$,
  not just $(y\_pred - y)$. Missing this gives the right direction but the
  wrong scale, which can slow convergence or require a different learning rate.

- **Updating X**: `dL_dX` is computed but not used for an update — `X` is
  input data, not a parameter. Only `W` and `b` are updated.

- **In-place vs copy**: `sgd_step` should modify `W` and `b` in-place
  (`W -= ...`). Returning new arrays and forgetting to reassign is a common bug.

- **Seed placement**: call `np.random.seed(42)` before both the dataset
  generation and the parameter initialisation to get reproducible results.

## Sanity Checks

After training, verify:

1. The loss at step 99 is much lower than at step 0.
2. `W` is close to the true weights `[[2.0], [-1.0]]`.
3. `b` is close to the true bias `[0.5]`.

If the loss increases or diverges, your gradient formula likely has the wrong
sign — check that you are using `(y_pred - y)` (not `(y - y_pred)`) and
subtracting (not adding) in the SGD update.

## Next Steps

This is backprop for a 1-layer network. In the next problem, you will build a
`Scalar` autograd engine that computes these gradients automatically by
recording the computation graph during the forward pass.
