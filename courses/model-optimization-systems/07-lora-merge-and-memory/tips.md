# Hints

Work in TODO order. Parts 1 through 3 are the module itself; parts 4 and 5 are
accounting on top of it. Get `adapter is a no-op at step 0: True` printing before
you touch anything else, because every later part assumes the module is built
correctly.

## Shapes first

With `in_features = out_features = 1024`, `rank = 8`, `batch = 32`:

| Tensor | Shape |
|---|---|
| `x` | `(32, 1024)` |
| `base.weight` | `(1024, 1024)` |
| `lora_A` | `(8, 1024)` |
| `lora_B` | `(1024, 8)` |
| `x @ lora_A.T` | `(32, 8)` |
| `(x @ lora_A.T) @ lora_B.T` | `(32, 1024)` |
| `lora_B @ lora_A` | `(1024, 1024)` |

If a transpose is wrong you will usually get a shape error rather than a wrong
answer, which is the good case. The bad case is a square layer like this one,
where `(1024, 1024)` matches in both orientations — so check part 2's difference,
not just that the code runs.

## Building the module

```python
self.base = torch.nn.Linear(in_features, out_features, bias=False)
self.base.weight.requires_grad_(False)

self.lora_A = torch.nn.Parameter(torch.empty(rank, in_features))
self.lora_B = torch.nn.Parameter(torch.zeros(out_features, rank))
torch.nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
```

`torch.nn.Parameter` is what registers these in `layer.parameters()`, which parts
3 and 4 rely on. A plain tensor attribute would still train if you passed it to
an optimizer by hand, but it would silently vanish from the parameter counts.

`requires_grad_(False)` goes on `base.weight`, not on `base`. Modules do not have
a `requires_grad` flag; only tensors do. `base.requires_grad_(False)` happens to
work because `nn.Module.requires_grad_` recurses into parameters, but writing it
on the tensor makes the intent explicit.

## The forward path

```python
down = x @ self.lora_A.T          # (32, 1024) -> (32, 8)
up = down @ self.lora_B.T         # (32, 8) -> (32, 1024)
return self.base(x) + self.scaling * up
```

Two small matmuls, `32x1024x8` and `32x8x1024`, against the base layer's
`32x1024x1024`. Do not compute `self.lora_B @ self.lora_A` inside `forward`.
Materializing the `(1024, 1024)` delta on every step throws away the entire
compute advantage and allocates a full-size tensor into the autograd graph.

## Merging

```python
def merged_weight(self):
    return self.base.weight + self.scaling * (self.lora_B @ self.lora_A)
```

Here forming the full delta is exactly right, because it happens once at
deployment rather than once per forward pass.

## Common mistakes

- Initializing `lora_B` with `torch.randn` instead of `torch.zeros`. Part 1 then
  fails, and every later number shifts.
- Initializing both factors to zeros. Part 1 passes, but the adapter is stuck:
  with $A = B = 0$ both gradients are zero, so it never leaves the origin.
- Writing `torch.empty(in_features, rank)` for `lora_A`. On a square layer the
  shapes still line up and nothing raises, but the merge check drifts.
- Computing the delta inside `forward`.
- Forgetting `self.scaling` in one of the two paths. Part 2 then reports a large
  difference — that is the check doing its job.
- Using bare `torch.allclose` in part 2. The default `atol=1e-8` is tighter than
  float32 rounding on a 1024-wide reduction, so a correct implementation can
  report `False`. Pass `rtol=1e-4, atol=1e-4`.
- Checking `base.weight.requires_grad` but not `base.weight.grad is None`. The
  flag is the intent; the `None` is the evidence.
- Calling `.backward()` inside `torch.inference_mode()`. Autograd records nothing
  there, so the grads stay `None`.
- Omitting the resident frozen base weights from the LoRA memory total. That
  turns a real 3.82x into a fictional 65x.
- Hardcoding `4` as the element size. Use `element_size()`; the whole point of the
  accounting is that it follows the tensors.

## Sanity checks

Copy these from a passing run, not from intuition:

- `scaling alpha/r` is `2.000` — the same ratio the theory module uses, reached
  from `r = 8, alpha = 16` rather than `r = 2, alpha = 4`.
- `max abs diff vs frozen base` is `0.00000` and `adapter is a no-op at step 0` is
  `True`. This one is genuinely exact; the raw value is `0.0`.
- `max abs diff merged vs adapter path` is `0.00000` and `merge is equivalent` is
  `True`. The raw difference here is about `1.4e-06`, which is float32 rounding
  over a 1024-term sum, not a bug.
- `frozen params: 1048576`, `trainable params: 16384`, `trainable percent: 1.538`.
  That is $8 \times 2048$ trainable against $1024^2$ frozen.
- `base weight bytes: 4194304` and `adapter weight bytes: 65536`.
- `full fine-tune total bytes: 17039360` versus `LoRA total bytes: 4456448`.
- `trainable-state ratio: 65.00` but `total training memory ratio: 3.82`. The
  first is $1064960/16384$; the second is what actually fits on the device.
- The rank sweep runs `0.8516, 0.7250, 0.5245, 0.2923, 0.1306, 0.1052, 0.0989`
  for r = 1, 2, 4, 8, 16, 32, 64.

## Reading the rank sweep

This is the payoff, so do not skip it.

Error falls steeply from rank 1 to rank 16 — `0.8516` down to `0.1306`, nearly a
factor of seven — and then almost stops. Doubling from 32 to 64 moves it from
`0.1052` to `0.0989`, about 6%, while doubling the adapter to 131,072 parameters.

The shape comes entirely from the target's spectrum. `build_target_delta` sums 48
outer products with geometrically decaying weights (`0.85**k`) and adds a small
isotropic noise term. The normalized top singular values print as
`1.0000 0.8521 0.7310 0.6145 0.5011`, tracking that decay. Truncating at rank r
discards the tail energy, so as long as the spectrum is decaying, each extra rank
removes a meaningful chunk. Once the rank has absorbed the structured component,
what remains is the noise floor, and noise has a flat spectrum — no low-rank
matrix approximates it, at any rank you can afford.

Two consequences worth carrying forward:

1. `svd_rel_err` is a *ceiling*, not a measurement of training. It is what the
   best possible rank-r matrix achieves, by Eckart-Young. A real fine-tune lands
   at or above this line, never below it.
2. "Is rank 8 enough?" is not a question about LoRA. It is a question about how
   fast your target delta's singular values decay, and the only way to answer it
   for a given model and task is to look.

## Going deeper

Things worth trying after the grader passes:

- Set `TARGET_DECAY` to `0.99` and re-run. The spectrum flattens, and the sweep
  stops rewarding rank — a direct demonstration that the curve belongs to the
  target, not to the method.
- Set `TARGET_NOISE` to `0.0` and watch the plateau disappear. The delta then has
  exact rank 48, so the error keeps falling all the way to zero instead of
  flattening out around `0.10`.
- Change `ALPHA` to `8` so `scaling` becomes `1.0`. Part 1 is unaffected — zero
  times any scale is still zero — which is a useful reminder that the no-op
  property does not depend on the hyperparameter.
- Attach a real `torch.optim.Adam` to `layer.parameters()` versus to only the
  adapter parameters, step both once, and compare `len(optimizer.state)`. The
  byte accounting in part 4 stops being a model and becomes an observation.
- Merge the adapter into a *quantized* base using the INT4 code from module 04:
  dequantize, add the delta, requantize. The merge identity holds in exact
  arithmetic but not after requantization, which is why QLoRA-style pipelines
  treat merging as a lossy step.

## References

- Hu, Shen, Wallis, Allen-Zhu, Li, Wang, Wang, and Chen, *LoRA: Low-Rank
  Adaptation of Large Language Models* (2021), arXiv:2106.09685 — introduces the
  method, the $\alpha/r$ scaling, and the zero-initialized $B$.
- Dettmers, Pagnoni, Holtzman, and Zettlemoyer, *QLoRA: Efficient Finetuning of
  Quantized LLMs* (2023), arXiv:2305.14314 — 4-bit NF4 base weights, double
  quantization, and paged optimizers.
- Eckart and Young, *The approximation of one matrix by another of lower rank*
  (1936) — the theorem that makes the truncated SVD the optimal rank-r
  approximation in Frobenius norm.
- Liu, Wang, Yin, Molchanov, Wang, Cheng, and Chen, *DoRA: Weight-Decomposed
  Low-Rank Adaptation* (2024), arXiv:2402.09353 — splits the update into
  magnitude and direction.
- Hugging Face PEFT documentation, https://huggingface.co/docs/peft — the
  production implementation of everything above, including `merge_and_unload`.
