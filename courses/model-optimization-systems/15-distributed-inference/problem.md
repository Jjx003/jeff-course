# Distributed inference: TP, PP, and MoE

This course has been quietly cheating. Module 2 computed decode floors for a 70B
model on "one H100," and every module since has reused that framing. But a 70B
model in BF16 is 140 GB of weights, and an H100 has 80 GB of HBM. The machine
the whole course has been reasoning about cannot hold the model the whole course
has been reasoning about. Every production deployment of a model in this class
is a **distributed** deployment, and the single-GPU roofline was always a
simplification.

This module pays off that debt. The good news is that nothing from the earlier
modules is wasted: distributed inference is the same roofline arithmetic with
one new term — **communication** — and the same discipline applies. Derive the
floor, find the term that dominates, and be suspicious of any speedup claim that
does not say which term it shrank.

There are three standard ways to cut a transformer across GPUs, and they cut
along different axes:

| Strategy | What is sharded | What crosses the wire | What it buys |
|---|---|---|---|
| Tensor parallel (TP) | every weight matrix, within a layer | activations, twice per layer | lower per-token latency |
| Pipeline parallel (PP) | whole layers, in stages | activations, once per stage boundary | capacity with cheap links |
| Expert parallel (EP) | experts of an MoE layer | routed tokens, twice per MoE layer | capacity for sparse models |

The rest of this reading derives when each one wins.

## Tensor parallelism: two ways to cut a matmul

Take one linear layer $Y = XW$ with $W$ of shape $d_\text{in} \times
d_\text{out}$, and $p$ GPUs. There are exactly two clean cuts.

**Column parallel.** Split $W$ by output columns: $W = [W_1 \mid W_2 \mid \dots
\mid W_p]$. Every GPU holds the full input $X$ and computes $Y_i = XW_i$ — a
$1/p$ slice of the output. No communication happened, but the output is now
scattered across GPUs.

**Row parallel.** Split $W$ by input rows, so GPU $i$ holds $W^{(i)}$ of shape
$(d_\text{in}/p) \times d_\text{out}$ and only the matching slice $X^{(i)}$ of
the input. Each GPU computes a **partial sum** $Y^{(i)} = X^{(i)}W^{(i)}$ of the
full output, and the true result is $Y = \sum_i Y^{(i)}$. That sum is an
**all-reduce**: every GPU ends up with the complete $Y$.

Neither cut is interesting alone. The trick — due to Megatron-LM — is the
pairing. An MLP block is two matmuls with a nonlinearity between them:

$$
Y = \sigma(XW_\text{up})\,W_\text{down}
$$

Cut $W_\text{up}$ by columns and $W_\text{down}$ by rows. The column cut leaves
each GPU with a slice of $\sigma$'s input — and because $\sigma$ is elementwise,
each GPU can apply it locally. That slice is exactly the input the row cut
wants. The whole block runs on shards and needs **one all-reduce, at the very
end**.

![Column-parallel then row-parallel MLP across four GPUs, with the single all-reduce at the output and the elementwise nonlinearity applied locally to each shard](/courses/model-optimization-systems/dist-tensor-parallel.svg)

Attention shards even more naturally: heads are independent until the output
projection, so each GPU takes $H_q/p$ query heads (and $H_{kv}/p$ KV heads),
runs attention locally, and the output projection is row-parallel — again one
all-reduce. A full transformer layer is therefore **two all-reduces per token**:
one after attention, one after the MLP.

The order matters and the coding module will make you prove it. Cutting
row-first would put partial sums *into* the nonlinearity, and
$\sigma(a) + \sigma(b) \ne \sigma(a+b)$ — the cheap cut and the correct cut are
different cuts, and the difference is not a rounding error.

## What the all-reduce costs

An all-reduce of $n$ bytes per GPU over $p$ GPUs is well modeled by two terms —
a fixed latency $\alpha$ per collective and a bandwidth term. Ring all-reduce
moves $2\,\frac{p-1}{p}\,n$ bytes through each GPU's links:

$$
t_\text{ar} \approx \alpha + \frac{2(p-1)}{p}\cdot\frac{n}{\beta_\text{link}}
$$

Now put decode-shaped numbers in. At batch 1, the activation being reduced is
one token's hidden vector: $n = 8192 \times 2$ bytes $= 16$ KB for a 70B model.
Over NVLink at 450 GB/s the bandwidth term is about **60 nanoseconds**. The
latency term $\alpha$ — kernel launch, synchronization across eight ranks,
protocol overhead — is measured in **microseconds**, typically 5–15 µs for a
small NVLink all-reduce. The bandwidth term is irrelevant; decode collectives
are pure latency.

That changes how you read the layer count. Eighty layers times two all-reduces
is **160 collectives per generated token**. At 10 µs each, that is 1.6 ms of
communication per token that does not shrink as you add GPUs. Meanwhile the
thing TP actually parallelizes — the weight read — is 41.79 ms at TP 1 and
$41.79/p$ ms at TP $p$, because each GPU streams only its shard:

$$
t_\text{step}(p) \approx \frac{41.79\ \text{ms}}{p} + 1.6\ \text{ms}
$$

![Decode step floor and effective speedup against tensor-parallel degree, showing the fixed collective-latency term flattening the curve](/courses/model-optimization-systems/dist-tp-decode-scaling.svg)

At TP 8 the floor is about 6.8 ms rather than the ideal 5.2 ms — an effective
speedup of 6.1× on eight GPUs. This is Amdahl's law with the serial term played
by collective latency, and it is why TP is almost always confined to the 8-GPU
NVLink island inside one server. Across InfiniBand between nodes, $\alpha$
roughly triples and $\beta_\text{link}$ drops by an order of magnitude, and the
flat term eats the scaling entirely.

Prefill inverts the picture. A 2048-token prompt makes $n = 2048 \times 16$ KB
$= 32$ MB per all-reduce, the bandwidth term is now ~125 µs against a compute
time of a few hundred microseconds per layer, and communication is a
percentage-level tax rather than a floor. Same model, same GPUs, same
collectives — different regime, because the payload scales with tokens and
decode has one.

## What TP does to the KV cache

Module 11 established that decode attention is irreducibly memory-bound and the
KV cache is the object being managed. TP interacts with it directly: KV heads
shard across GPUs, so each GPU stores $H_{kv}/p$ heads' worth of cache and
**the per-GPU cache shrinks by $p$** — attention itself needs no extra
communication, because each GPU's query heads only ever read its local KV heads.

But the shrinking stops at $p = H_{kv}$. A Llama-3-70B has 8 KV heads. At TP 8,
each GPU holds exactly one; at TP 16 the KV heads must be **replicated**, and
the cache stops scaling even though the weights keep sharding. GQA, which
module 11 presented as a cache compression, is also a **cap on useful tensor
parallelism** — the two decisions were made in the same room. This is a real
constraint: it is one reason TP 8 is the standard deployment for 70B-class
models and why going wider forces a different strategy.

## Pipeline parallelism: capacity without latency

PP cuts by depth: GPU 0 holds layers 0–19, GPU 1 holds 20–39, and so on.
Between stages, only one token's activations cross the wire — 16 KB per
boundary, a few boundaries total, cheap enough for ethernet. That is PP's
appeal: it scales past the NVLink island with almost no bandwidth requirement.

The cost is structural. A token must traverse the stages **in order**, so the
per-token decode latency is the *sum* of the stage times — reading $1/p$ of the
weights $p$ times in sequence takes as long as reading all of them once. PP
does not reduce inter-token latency at all. What it buys is throughput: while
your token is in stage 3, other requests' tokens occupy stages 0–2, and the
pipeline commits $p$ tokens' work per step once full.

When the pipeline is *not* full, you pay the **bubble**. With $p$ stages and
$m$ microbatches in flight, the fill-and-drain overhead is

$$
\text{bubble fraction} = \frac{p-1}{m + p - 1}
$$

— derived in the theory notes. At $m = p$, over a third of the machine-time is
idle; at $m = 4p$ it is under 20 percent. The rule of thumb that follows: PP is
a **throughput** tool that needs deep concurrency to amortize its bubble, TP is
a **latency** tool that needs fast links to amortize its collectives, and
production systems compose them — TP 8 inside each node, PP across nodes.

## Mixture of experts: the batching math changes

MoE replaces each MLP with $E$ expert MLPs and a router that sends each token
to $k$ of them. Mixtral 8×7B has 47B parameters of which ~13B are active per
token ($E = 8$, $k = 2$); DeepSeek-V3 has 671B with 37B active ($E = 256$
routed, $k = 8$). The pitch is that quality tracks total parameters while
FLOPs track active parameters.

Module 1 derived decode arithmetic intensity as $I = 2B/b$ — but that
derivation assumed every loaded weight serves every sequence in the batch. MoE
breaks exactly that assumption, and it breaks it in both directions.

**At batch 1, MoE wins.** Only the $k$ routed experts are read, so the
per-token weight traffic is the *active* parameters, not the total. Mixtral
decodes with roughly the weight-read floor of a 13B model while representing
47B parameters' worth of capacity.

**At batch $B$, the win dilutes.** Different tokens route to different experts,
so the batch must load the *union* of routed experts. With uniform routing, the
expected number of distinct experts touched per layer is

$$
m(B) = E\left(1 - \left(1 - \tfrac{k}{E}\right)^{B}\right)
$$

and the expert arithmetic intensity becomes

$$
I_\text{MoE} = \frac{2Bk}{m(B)\,b}
\quad\xrightarrow{\ B\ \text{large}\ }\quad \frac{k}{E}\cdot\frac{2B}{b}
$$

The large-$B$ slope is the dense slope times $k/E$. Batching still buys reuse,
but each unit of batch buys $E/k$ times less of it, so the batch needed to
reach the H100 ridge point of 295 moves from **295** (dense BF16) to about
**1,180** for Mixtral and about **9,440** for a DeepSeek-V3-shaped model.

![Expected distinct experts touched versus batch size, and MoE decode arithmetic intensity versus batch compared with dense, with ridge-point crossings marked](/courses/model-optimization-systems/moe-decode-intensity.svg)

That number is the entire economics of MoE serving in one line. A dense model
saturates its GPU at batches a single replica sees routinely. An MoE model
needs thousands of concurrent tokens to stop being a memory-bandwidth machine —
more than fit on one node — which is why serious MoE serving uses **expert
parallelism**: spread the $E$ experts across many GPUs, and route tokens to
their experts with an **all-to-all** exchange (one to dispatch, one to combine,
per MoE layer). The aggregate batch of the whole cluster, not one GPU, is what
climbs the roofline.

All-to-all brings its own failure mode: the collective finishes when the
slowest rank finishes, so a **hot expert** — one that this batch's tokens
disproportionately chose — makes every GPU wait. Routers are trained with
auxiliary losses to balance load, and serving systems cap tokens per expert
(the capacity factor) or replicate hot experts. The theory notes work an
example: with 256 experts across 32 GPUs, a 2× imbalance on one rank halves
effective all-to-all bandwidth for the entire step.

## Protein models: mostly the other regime

It is worth being precise about why this module's machinery matters less for
the protein workloads in the next module. ESMFold's language-model trunk is
~15B parameters (30 GB BF16) and AlphaFold2's Evoformer is under 100M — these
fit on one GPU with room to spare, so *weight* sharding solves a problem they
do not have. Their scaling problem is **activation** memory: the $O(L^2)$ pair
representation and the $O(L^3)$ triangle intermediates. The distributed answer
there is data parallelism for throughput (replicate the model, shard the
protein list) and, for extreme complexes, sharding the pair *activations*
across devices — which looks more like sequence/context parallelism than like
Megatron TP. Same accounting discipline; the tensor that will not fit is a
different tensor.

## Recap

Distributed inference adds one word to the roofline vocabulary —
communication — and everything else follows from where each strategy pays it.
TP pays per layer in latency-dominated collectives, buys per-token speed, and
stops scaling at the NVLink island and the KV-head count. PP pays almost
nothing per boundary, buys capacity and throughput, and cannot reduce
inter-token latency by construction. EP pays two all-to-alls per MoE layer and
is mandatory once the batch a single GPU can hold is too small to feed a sparse
model's roofline.

The next module makes the TP half concrete: you will shard a transformer block
across simulated devices, count every byte the collectives move, show the
block needs exactly two all-reduces, prove the sharded output matches the
unsharded one — and measure what happens if you cut the MLP the wrong way.
