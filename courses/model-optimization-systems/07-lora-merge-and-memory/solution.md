# Solution walkthrough

## The module is three lines of algebra and one initialization decision

`LoRALinear` holds a frozen `nn.Linear` and two parameters. `forward` computes
the base path plus two small matmuls; `merged_weight` computes the base weight
plus the full delta. Everything else in the file is measurement.

The one design decision that carries real weight is `torch.zeros` for `lora_B`.
It makes the adapter an exact no-op, and the output shows exactly that:

```text
max abs diff vs frozen base: 0.00000
adapter is a no-op at step 0: True
```

That `0.00000` is not a rounded small number — the raw difference is `0.0`, which
is why the check uses `torch.allclose(..., rtol=0.0, atol=0.0)` rather than a
tolerance. Zero times anything is zero, so the adapter term contributes nothing
before it contributes something.

The asymmetry between the two factors is the part worth internalizing. Zeroing
both would also give a no-op, but then $\partial L/\partial A$ and
$\partial L/\partial B$ are both zero and the adapter is pinned at the origin
forever. Randomizing both would give a working gradient path but would perturb
the pretrained function before training had learned anything. Zeroing exactly one
gets both properties: identity at step 0, live gradients at step 1.

## The merge check is the module's central claim

```text
max abs diff merged vs adapter path: 0.00000
merge is equivalent: True
```

The raw maximum difference is about `1.4e-06`. That is float32 rounding across a
1024-term dot product, and it is why part 2 uses `rtol=1e-4, atol=1e-4` while
part 1 uses exact equality. The distinction is worth being explicit about: part 1
is an algebraic zero, part 2 is an algebraic identity evaluated in inexact
arithmetic. Bare `torch.allclose` with its default `atol=1e-8` would be tighter
than float32 can deliver here, and a correct implementation would report `False`.

What the identity buys is a deployment choice with no accuracy cost. Serving the
merged weight is one matmul of the original shape — same kernel, same graph, no
adapter tensors resident. Keeping the adapter separate costs two extra small
matmuls per layer and buys the ability to serve many tenants off one base model.
Because the outputs agree to $10^{-6}$, that decision is purely about systems, not
about quality.

## Frozen means `grad is None`

```text
base.weight requires_grad: False
base.weight grad is None: True
lora_A grad shape: (8, 1024)
lora_B grad shape: (1024, 8)
frozen params: 1048576
trainable params: 16384
trainable percent: 1.538
```

`requires_grad: False` states the intent; `grad is None` is the evidence that
autograd honored it. The second one matters because it is what an optimizer keys
on. A parameter that still accumulates a gradient gets optimizer state allocated
for it, and the memory story in part 4 quietly disappears.

Note that this backward pass happens after `lora_B` has been filled. At
initialization the adapter is a no-op, and $\partial L/\partial A$ is proportional
to $B$, so `lora_A.grad` would be exactly zero on the very first step. It becomes
nonzero as soon as $B$ moves, which is precisely what the first optimizer step
does.

## The memory numbers, and the honest ratio

```text
base weight bytes: 4194304
adapter weight bytes: 65536
full fine-tune total bytes: 17039360
LoRA total bytes: 4456448
trainable-state ratio: 65.00
total training memory ratio: 3.82
```

Every one of those is derived from `numel() * element_size()`. Adam holds three
tensors per trainable parameter beyond the parameter itself — gradient,
`exp_avg`, `exp_avg_sq` — so full fine-tuning costs $4 \times$ the weight bytes
and LoRA pays that multiplier on 16,384 entries instead of 1,064,960.

The two ratios are the point of this section. Trainable state shrinks by
$1064960/16384 = 65\times$, and that number is real. It is also not the number
your GPU sees, because the frozen base weights are still resident: you cannot run
a forward pass without them. Counting them gives `3.82x` for the whole training
footprint.

Both are honest; only one answers "will this fit". A claim of "LoRA cuts memory
65x" is quoting the first while implying the second. This is also exactly the gap
QLoRA attacks — not by shrinking the adapter further, but by quantizing the
`4194304` bytes of resident base weight that dominate the LoRA column.

## The rank sweep measures the ceiling, not the training

```text
top 5 normalized singular values: 1.0000 0.8521 0.7310 0.6145 0.5011
  r=1   trainable=2048    trainable%=0.195   svd_rel_err=0.8516
  r=2   trainable=4096    trainable%=0.389   svd_rel_err=0.7250
  r=4   trainable=8192    trainable%=0.775   svd_rel_err=0.5245
  r=8   trainable=16384   trainable%=1.538   svd_rel_err=0.2923
  r=16  trainable=32768   trainable%=3.030   svd_rel_err=0.1306
  r=32  trainable=65536   trainable%=5.882   svd_rel_err=0.1052
  r=64  trainable=131072  trainable%=11.111  svd_rel_err=0.0989
```

No training happens here, and that is deliberate. By Eckart-Young the truncated
SVD is the optimal rank-$r$ approximation in Frobenius norm, so `svd_rel_err` is
a floor on the error of *any* rank-$r$ adapter for this target. A real fine-tune
lands on or above that line. Measuring the ceiling separates "my rank is too
small" from "my optimizer is not converging", which are otherwise easy to
confuse.

The curve has two regimes. From rank 1 to rank 16 the error drops by nearly a
factor of seven, because `build_target_delta` sums 48 outer products with weights
`0.85**k` and each additional rank removes a real chunk of that decaying energy —
visible directly in the printed singular values. From rank 32 to 64 it moves only
from `0.1052` to `0.0989` while doubling the parameter count, because what
remains is the isotropic noise term, whose spectrum is flat. Flat spectra are not
low-rank approximable at any budget you would accept.

So the generalizable statement is not "rank 16 is enough." It is that the useful
rank is set by where the target delta's singular values stop decaying, and that
this is a property of the model and task rather than of LoRA. The LoRA paper's
empirical claim — that adaptation deltas have low intrinsic rank — is the
assertion that real deltas look like the left half of this table.

## Where this goes next

- Merging into a quantized base is not free: dequantize, add, requantize
  introduces error that the exact merge identity does not cover. QLoRA-style
  pipelines usually keep the adapter separate for this reason.
- Multi-adapter serving inverts the trade in this module. When hundreds of
  adapters share one base, the two extra matmuls are cheap and merging is
  impossible, so the bottleneck moves to routing and batching requests with
  different adapters.
- DoRA and related methods keep this structure and change what the low-rank term
  parameterizes, decomposing the update into magnitude and direction rather than
  adding a raw delta.
