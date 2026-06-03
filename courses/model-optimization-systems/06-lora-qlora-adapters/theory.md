# Parameter count and memory

For a dense matrix:

$$
\text{params}(W) = d_\text{out}d_\text{in}
$$

For a LoRA adapter:

$$
\text{params}(\text{LoRA}) = r(d_\text{in} + d_\text{out})
$$

The ratio is:

$$
\frac{r(d_\text{in}+d_\text{out})}{d_\text{in}d_\text{out}}
$$

For a square matrix with $d_\text{in}=d_\text{out}=d$, this simplifies to:

$$
\frac{2r}{d}
$$

So with $d=4096$ and $r=16$:

$$
\frac{2 \times 16}{4096} \approx 0.0078
$$

or about 0.78 percent of the dense matrix's parameter count.

## Where adapters are inserted

LoRA is usually applied to selected linear projections, such as:

| Transformer component | Why adapt it? |
|---|---|
| query projection | changes what the model attends to |
| value projection | changes what information is carried forward |
| output projection | changes how attention results mix |
| MLP up/down projections | changes feature transformations |

Adapting more matrices increases capacity and memory. Adapting fewer matrices
is cheaper and may be enough for narrow tasks. Rank, target modules, alpha, and
dropout are all part of the adapter design.

## Merge or dynamic adapter?

A LoRA adapter can be merged into the base matrix:

$$
W_\text{merged} = W + \frac{\alpha}{r}BA
$$

After merging, inference uses an ordinary dense matrix. This is fastest for a
single fixed adapter, but it creates one merged copy per variant.

Dynamic adapters keep $W$, $A$, and $B$ separate and apply the low-rank update
at inference time. This preserves flexibility but adds runtime work and
batching complexity.

| Choice | Best when | Cost |
|---|---|---|
| merge | one adapter is fixed for deployment | extra merged copies |
| dynamic | many adapters share one base | adapter routing and overhead |
| hot/cold hybrid | a few popular adapters dominate traffic | operational complexity |

## QLoRA memory intuition

If a 70B model is stored in 4-bit form, the raw weight storage is roughly:

$$
70 \times 10^9 \times 0.5 = 35 \text{ GB}
$$

Metadata, optimizer state, activations, gradients for adapters, and framework
overhead add more. Still, this is a different world from BF16 full fine-tuning,
where raw weights alone are about 140 GB and optimizer state can multiply the
requirement.

QLoRA's trick is not only "4-bit weights." It is the combination:

1. keep the base model frozen and quantized;
2. dequantize as needed for computation;
3. train small higher-precision adapters;
4. use optimizer and memory-management techniques that avoid spikes.

## Adapter composition and routing

Once adapters are small, systems start treating them as deployable artifacts.
That creates new patterns:

- per-customer adapters for enterprise behavior;
- task adapters for summarization, coding, retrieval, or classification;
- domain adapters for medicine, law, chemistry, or protein biology;
- routing policies that choose an adapter from the prompt or metadata;
- adapter libraries that can be loaded, evicted, or cached.

Composition is tempting but tricky. Adding two adapters is not guaranteed to
combine their behaviors cleanly. Training order, target modules, rank, and data
distribution all matter. In safety-critical domains, adapter composition needs
the same evaluation discipline as a new model.

## Serving cost model

A dynamic LoRA adapter adds two low-rank matmuls around a base projection:

$$
y = Wx + \frac{\alpha}{r}B(Ax)
$$

The base term costs roughly:

$$
2d_\text{out}d_\text{in}
$$

FLOPs for one vector. The LoRA path costs roughly:

$$
2r d_\text{in} + 2d_\text{out}r
$$

FLOPs. With small $r$, that is much cheaper than another dense matrix, but it
is not zero. It can also introduce extra memory reads, layout changes, or
kernel launches if the serving stack does not fuse the adapter path well.

This is why merged adapters remain attractive for hot deployments. If one
adapter receives most traffic, merging removes the dynamic low-rank branch from
the serving path. If thousands of adapters are rarely used, keeping them
separate avoids storing thousands of full merged models. A mature serving
system often uses a hybrid: merge the hottest adapters, keep warm adapters in
GPU memory, and offload cold adapters to CPU or disk.

## Relationship to quantization

Adapters and quantization can be combined in several ways:

| Setup | Base weights | Adapter weights | Use case |
|---|---|---|---|
| LoRA | BF16/FP16 | BF16/FP16 | simple PEFT |
| QLoRA | 4-bit | BF16/FP16 | memory-limited fine-tuning |
| LoftQ-style | quantized | initialized to offset quant error | better low-bit start |
| merged adapter | possibly re-quantized | folded into base | fixed deployment |

The hard part is preserving quality after all transformations. If you train an
adapter against one quantized base and then merge or re-quantize differently,
you should re-evaluate. The adapter learned in the numerical environment it
saw during training.

## Protein-model deployment

In protein modeling, adapters are especially useful when labeled data is small.
The base model learns broad sequence regularities from millions or billions of
sequences. The adapter learns a narrower mapping from those representations to
an assay or family. Good evaluation should ask:

- Are train and test proteins homologous?
- Does the adapter generalize to unseen families?
- Does it preserve calibration, not just rank order?
- Does it help the downstream wet-lab decision?
- Does quantizing the base change the adapter's conclusions?

Those questions are systems questions as much as ML questions. The deployment
artifact is not "a model"; it is base weights, quantization metadata, adapter
weights, tokenizer or alphabet, preprocessing, and evaluation assumptions.
