# LoRA, QLoRA, and adapter systems

Full fine-tuning changes every weight in a model. LoRA changes the update rule.
Instead of learning a dense update $\Delta W$ for a weight matrix $W$, LoRA
writes:

$$
W' = W + \frac{\alpha}{r}BA
$$

where:

- $W$ has shape $d_\text{out} \times d_\text{in}$,
- $A$ has shape $r \times d_\text{in}$,
- $B$ has shape $d_\text{out} \times r$,
- $r$ is the adapter rank,
- $\alpha$ is a scaling hyperparameter.

If $r$ is small, the adapter has far fewer trainable parameters than $W$:

$$
\text{params}(\text{LoRA}) = r(d_\text{in}+d_\text{out})
$$

instead of:

$$
\text{params}(W) = d_\text{out}d_\text{in}
$$

For a square $4096 \times 4096$ matrix and rank 16, the dense matrix has over
16 million parameters while the LoRA adapter has about 131 thousand. That is
less than 1 percent for that matrix.

## Why a rank-16 update is not obviously absurd

The arithmetic above is trivial. The interesting question is why constraining
$\Delta W$ to rank 16 does not destroy the fine-tune, and the answer comes from
two separate places.

The empirical half is **intrinsic dimensionality**. Aghajanyan and colleagues
showed that a pretrained model can be fine-tuned inside a randomly chosen
low-dimensional subspace and still reach 90 percent of full fine-tuning
performance — for RoBERTa-large on MRPC, a few hundred dimensions suffice out of
355 million. Their more surprising finding is the direction of the trend: the
*larger* the pretrained model, the *lower* its intrinsic dimension. Pretraining
does not just supply features; it compresses the space of updates that
adaptation needs to search.

The mathematical half is **Eckart–Young–Mirsky**. For any matrix $M$, the best
rank-$r$ approximation under the Frobenius norm is its truncated SVD, and the
residual is exactly the discarded spectrum:

$$
\min_{\operatorname{rank}(\hat{M}) \le r} \lVert M - \hat{M} \rVert_F^2
= \sum_{i > r} \sigma_i^2
$$

So a rank-$r$ adapter can represent an update well precisely when that update's
singular values decay quickly. The bet LoRA makes is that the $\Delta W$ needed
to specialize a pretrained model is a spectrally concentrated object — a few
strong directions, not 4096 comparable ones.

Two honest caveats, because this argument is often stated too strongly. First,
Eckart–Young bounds the best rank-$r$ approximation of a *known* $\Delta W$;
LoRA never computes that matrix. It constrains gradient descent to the rank-$r$
manifold from the start, which is a different and harder problem, and there is
no guarantee optimization finds the truncated-SVD solution. Second, the
low-rank bet is task-dependent. Adapting tone or format is plausibly low-rank.
Teaching a model a genuinely new domain — a new alphabet, a new modality, a
protein family unlike anything in pretraining — may not be, and the usual
symptom is that quality keeps improving as you raise $r$ instead of plateauing.
Rank is a hypothesis about your task, and a rank sweep is how you test it.

## Why this is a systems trick

LoRA is often introduced as a fine-tuning method, but it is also an
infrastructure primitive:

- one base model can serve many task-specific adapters;
- adapters can be swapped, merged, routed, versioned, or combined;
- QLoRA keeps the base model quantized while training adapters;
- inference can either apply adapters dynamically or merge them into base
  weights;
- adapter storage is small enough to make per-customer or per-task variants
  operationally realistic.

This changes the product shape. Instead of deploying ten full copies of a large
model, a team can deploy one base model plus ten small deltas. That saves
storage and memory, but it introduces new serving questions: which adapter is
active for this request, can requests with different adapters batch together,
and should hot adapters be merged for latency?

## What QLoRA changed

QLoRA combines:

- 4-bit base weights;
- higher-precision adapter weights;
- NF4 quantization for normally distributed weights;
- double quantization of scale metadata;
- paged optimizers to reduce memory spikes.

The base model is mostly frozen and compressed. The trainable state lives in
small adapter matrices. This makes useful fine-tuning possible on much smaller
hardware than full fine-tuning would require.

![Three-panel diagram contrasting full finetuning, LoRA, and QLoRA by where optimizer state, adapters, and base model weights live and how gradients flow](/courses/model-optimization-systems/lora-qlora-fig1-finetuning-memory.png)

*Figure 1 from Dettmers et al., QLoRA (CC BY 4.0). The three panels differ in
one structural way: how much of the picture the optimizer state occupies. In
full fine-tuning it is the largest object on the diagram. In LoRA it shrinks to
three small boxes. In QLoRA it shrinks further and can be paged out to CPU
under pressure, while the base transformer itself drops from 16-bit to 4-bit.*

### Where the memory actually goes

The reason that picture is shaped the way it is comes from a piece of
arithmetic worth memorizing. Full fine-tuning with Adam and BF16 mixed
precision costs roughly **16 bytes per parameter**:

| Component | Bytes per parameter |
|---|---:|
| BF16 weights | 2 |
| BF16 gradients | 2 |
| Adam first moment $m$ (FP32) | 4 |
| Adam second moment $v$ (FP32) | 4 |
| FP32 master weights | 4 |
| **Total** | **16** |

Apply that to a 65B model and compare the three regimes, excluding activations:

| Component | Full FT | LoRA | QLoRA |
|---|---:|---:|---:|
| base weights | 130 GB | 130 GB | 33.5 GB |
| base gradients | 130 GB | — | — |
| base Adam state | 520 GB | — | — |
| base FP32 master | 260 GB | — | — |
| adapter weights + state | — | ~1 GB | ~1 GB |
| **Total** | **~1040 GB** | **~131 GB** | **~35 GB** |

Read the columns as answering two different questions. LoRA's saving comes
almost entirely from deleting three rows — freezing the base removes gradients,
optimizer moments, and master weights in one move, and that is a 13× cut before
any quantization is involved. QLoRA then attacks the one row LoRA left standing.

Neither step is the whole trick, and the second only pays because the first
happened: quantizing the base to 4 bits would be pointless if you still had to
keep 520 GB of FP32 Adam state for it. That ordering is the actual insight, and
it is why "QLoRA is just 4-bit LoRA" undersells it.

By 2026, the adapter family is broader. DoRA separates magnitude and direction
updates. LoftQ initializes adapters to compensate for quantization error.
Low-bit PEFT work asks how far below 4 bits the base or adapters can go.
Serving systems increasingly care about multi-adapter batching, adapter
offloading, and routing rather than just training memory.

## Protein-model angle

Adapters are attractive for protein language models because biological tasks
are diverse:

- variant effect prediction;
- family-specific function prediction;
- binding-site prediction;
- mutation scoring;
- solubility or expression prediction;
- structure-aware downstream probes.

A general protein model may already encode useful evolutionary and structural
features. A small adapter can specialize those representations to one assay,
protein family, or laboratory objective. The danger is evaluation leakage:
random splits can put close homologs in both train and test. For biology,
adapter quality should be checked on held-out families, time splits, or
carefully separated assays when possible.

## Recap

LoRA is a low-rank update. QLoRA is a memory plan that trains adapters while
keeping the base model quantized. Adapter systems are a deployment architecture:
one base model, many small deltas, and a choice between merging for speed or
applying dynamically for flexibility.
