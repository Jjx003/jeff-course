# Merge LoRA and count the memory

The reading module described LoRA as a structured delta: freeze $W$, learn a
low-rank correction, and decide later whether to merge it or apply it
dynamically. Every claim in that description is a testable property of a real
`torch.nn.Module`. Now you will build the module and test them.

You will implement `LoRALinear`, which wraps a frozen
`torch.nn.Linear(1024, 1024, bias=False)` with a rank-8 adapter at
$\alpha = 16$, and run a batch of 32 through it. By the end you will have
established four things with measurements rather than assertions:

1. The adapter is an *exact* no-op at initialization.
2. The merged weight computes the same function as the two-matmul adapter path.
3. Gradients reach $A$ and $B$ and nothing else.
4. What LoRA actually saves in optimizer memory, and where its expressiveness
   ceiling comes from.

Graded output goes to stdout on CPU in float32 with `torch.manual_seed(0)`, so
your numbers match the grader's exactly. The program also prints two wall-clock
timings to **stderr**. Those are machine-dependent, so they are streamed to you
in the session log and are not graded.

## Part 1 — Initialization is an exact no-op

Build the module. The base layer's weight gets `requires_grad_(False)`. The
adapter is two parameters:

$$
A \in \mathbb{R}^{r \times d_\text{in}}, \qquad
B \in \mathbb{R}^{d_\text{out} \times r}
$$

Initialize $A$ with `torch.nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))`,
which is what `nn.Linear` uses for its own weight, and initialize $B$ to
**zeros**. Then `forward` computes:

$$
y = Wx + \frac{\alpha}{r}B(Ax)
$$

Because $B = 0$, the second term is exactly zero — not small, zero — so the
adapted layer and the frozen base layer produce bit-identical outputs. Verify it
with `torch.allclose(..., rtol=0.0, atol=0.0)` and print the maximum absolute
difference.

This matters more than it looks. Fine-tuning starts from the pretrained function
rather than from a randomly perturbed one, so the first optimizer step improves a
model that already works. Initializing both factors randomly would inject noise
into every forward pass before training has learned anything, and the run would
have to spend its early steps undoing that.

## Part 2 — The merged weight equals the adapter path

`normal_` fills $B$ with seeded random values to simulate an adapter that has
been trained for a while. Implement `merged_weight`:

$$
W' = W + \frac{\alpha}{r}BA
$$

and check that the single merged matmul agrees with the two-matmul adapter path:

$$
xW'^{\top} \;\approx\; xW^{\top} + \frac{\alpha}{r}\left(xA^{\top}\right)B^{\top}
$$

This is the single most important claim in the reading module. Merging is only
free if it changes nothing, and "changes nothing" is a property you can measure
rather than trust.

Note the difference from part 1: this equality holds only up to float32 rounding,
because the two sides sum the same products in a different order. Use
`torch.allclose(..., rtol=1e-4, atol=1e-4)` and print the maximum absolute
difference, which should round to `0.00000` at five decimals. If you see anything
larger, your factor order or your transpose is wrong, not your arithmetic
precision.

## Part 3 — Gradient discipline

Run one real forward pass outside `inference_mode`, form `output.pow(2).mean()`,
and call `.backward()`. Then print the evidence:

- `base.weight.requires_grad` is `False` and `base.weight.grad is None`;
- `lora_A.grad` has shape `(8, 1024)` and `lora_B.grad` has shape `(1024, 8)`;
- both adapter gradients are nonzero.

`grad is None` is the load-bearing check. A frozen parameter that still receives
a gradient is a parameter the optimizer will allocate state for, and the memory
saving in part 4 evaporates.

Then split `layer.parameters()` by `requires_grad` and report frozen count,
trainable count, and trainable percentage of the total.

## Part 4 — Optimizer memory, computed from real tensors

Adam keeps three tensors per *trainable* parameter beyond the parameter itself:
the gradient, `exp_avg`, and `exp_avg_sq`. So a full fine-tune costs four bytes
of state per byte of weight, while LoRA pays that multiplier only on the adapter.

Implement `training_bytes` and derive every number from
`tensor.numel() * tensor.element_size()`. Never hardcode a byte count.

Be honest about the frozen base. It does not need a gradient or optimizer state,
but its weights are still resident in memory during training — you cannot run a
forward pass without them. Leaving them out of the LoRA total would report an
enormous saving that no one has ever observed. The program prints both ratios so
the difference is impossible to miss: one for trainable state alone, one for the
whole training footprint. They differ by more than an order of magnitude, and
only the second one is what your GPU sees.

## Part 5 — Where the rank ceiling comes from

Finally, sweep ranks 1 through 64 and report, for each, the adapter's trainable
parameter count, its percentage, and how well a rank-$r$ matrix can approximate a
*fixed* target weight delta.

For that last column, do not train anything. The Eckart-Young theorem says the
best possible rank-$r$ approximation in Frobenius norm is the truncated SVD, so
with singular values $s_1 \ge s_2 \ge \dots$ the optimal relative error is:

$$
\varepsilon(r) = \sqrt{\frac{\sum_{i > r} s_i^2}{\sum_i s_i^2}}
$$

That is a ceiling: no training procedure, no matter how good, does better at rank
$r$. Compute it with `torch.linalg.svdvals` and `truncation_errors`.

`build_target_delta` is given. It is a product of low-rank factors with a
geometrically decaying spectrum plus a small isotropic noise term, which is a
reasonable stand-in for a real fine-tuning delta. Watch what happens at the high
end of the sweep: the error stops improving once the rank has absorbed the
structured part and only noise is left. That plateau is the point. LoRA's
expressiveness limit is not a property of LoRA; it is a property of the target
delta's singular value spectrum.

Do not change the starter constants or the output labels. The grader compares
printed stdout.

## Recap

You now have a LoRA layer that provably starts as identity, merges without
changing its function, trains only its adapter, and reports its memory cost from
real tensors — plus a measured answer to "how much rank do I need?". The next
module is a timed drill that turns this kind of memory arithmetic into fast
mental estimation across weights, KV caches, and adapters.
