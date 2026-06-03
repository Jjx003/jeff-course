# Formulas

Most model-serving memory estimates reduce to:

$$
\text{values} \times \text{bytes per value}
$$

The hard part is counting the values without forgetting a dimension.

## Weight memory

For rough decimal GB:

$$
\text{GB} \approx \text{parameters in billions} \times \text{bytes per parameter}
$$

Common values:

| Format | Bytes per value | Mental shortcut |
|---|---:|---|
| FP32 | 4 | 7B is about 28 GB |
| BF16 / FP16 | 2 | 7B is about 14 GB |
| INT8 | 1 | 7B is about 7 GB |
| INT4 | 0.5 | 8B is about 4 GB |

Real checkpoints include scales, zero points, tensor metadata, possible unquantized layers, and framework overhead. The drill asks for raw estimates so the base arithmetic becomes automatic.

## LoRA adapter parameters

For one adapted matrix:

$$
\text{LoRA params} = r(d_\text{in}+d_\text{out})
$$

For a square $d \times d$ projection:

$$
2rd
$$

A rank-16 adapter on one $4096 \times 4096$ matrix is:

$$
2 \times 16 \times 4096 = 131072
$$

parameters, about 131k. If that adapter targets many projections across many layers, multiply by the number of adapted matrices.

## KV-cache memory

For one request:

$$
\text{bytes} =
L_\text{layers}
\times H_\text{kv}
\times D_\text{head}
\times 2
\times T
\times B_\text{dtype}
$$

where:

- $L_\text{layers}$ is the number of transformer layers,
- $H_\text{kv}$ is the number of key/value heads,
- $D_\text{head}$ is the head dimension,
- the factor of 2 accounts for key and value tensors,
- $T$ is the number of cached tokens,
- $B_\text{dtype}$ is bytes per stored value.

Grouped-query attention and multi-query attention reduce $H_\text{kv}$ relative to the number of query heads. That is one reason modern serving models often use GQA: decode is usually memory-bandwidth hungry, and fewer KV heads mean less cache to read and store.

## Padding waste

If a batch pads every sequence to the maximum length, then:

$$
\text{padded tokens} = N \times T_\text{max}
$$

and:

$$
\text{waste} =
\frac{\text{padded tokens} - \text{real tokens}}{\text{padded tokens}}
$$

This is why serving systems avoid naive static batching when requests have varied lengths. Padding waste is easy to ignore because the GPU still looks busy. The problem is that it is busy doing work that does not correspond to real user tokens.

## Unit discipline

The drill uses decimal MB/GB conventions because they make mental arithmetic cleaner:

$$
1\ \text{MB} \approx 10^6\ \text{bytes}
$$

$$
1\ \text{GB} \approx 10^9\ \text{bytes}
$$

Binary MiB/GiB are more exact in low-level allocator discussions. For planning conversations, decimal units are usually close enough as long as everyone is consistent.
