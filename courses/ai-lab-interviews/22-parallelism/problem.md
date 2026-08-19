# Parallelism and Distributed Training

"What is 5D parallelism?" is a real rapid-fire question, and the good answer is not a list. It is: here are the five things you can split, here is what each costs in communication, and here is the order you reach for them.

You are unlikely to be asked to implement a parallelism strategy in an interview. You are quite likely to be asked to reason about one.

## The five axes

| Axis | What is split | Communication | When to use it |
|---|---|---|---|
| **Data** | the batch | all-reduce of gradients, once per step | always, first |
| **Tensor** | matrices within a layer | all-reduce twice per layer | when a layer will not fit; keep inside one node |
| **Pipeline** | layers across devices | point-to-point activations at stage boundaries | across nodes, when the model will not fit |
| **Context** | the sequence | all-gather of K and V in attention | very long context |
| **Expert** | MoE experts | all-to-all token routing | MoE models |

## The prerequisite: collectives

Everything above is built from five operations. You should be able to describe each in one line and know its cost.

```mermaid
flowchart TB
  subgraph AR["all-reduce"]
    direction LR
    A1["a"] --> R1["a+b+c+d"]
    B1["b"] --> R2["a+b+c+d"]
    C1["c"] --> R3["a+b+c+d"]
    D1["d"] --> R4["a+b+c+d"]
  end
  subgraph AG["all-gather"]
    direction LR
    A2["a"] --> G1["abcd"]
    B2["b"] --> G2["abcd"]
    C2["c"] --> G3["abcd"]
    D2["d"] --> G4["abcd"]
  end
  subgraph RS["reduce-scatter"]
    direction LR
    A3["a1a2a3a4"] --> S1["sum of all _1"]
    B3["b1b2b3b4"] --> S2["sum of all _2"]
    C3["c1c2c3c4"] --> S3["sum of all _3"]
    D3["d1d2d3d4"] --> S4["sum of all _4"]
  end
```

The identity worth knowing: **all-reduce = reduce-scatter + all-gather**, and each half moves the same volume. That is why ZeRO stage 2 can shard gradients at no extra communication cost — it is already doing both halves.

## What gets asked

- What is 5D parallelism? Which do you reach for first?
- Why does tensor parallelism have to stay inside a node?
- What is the pipeline bubble and how do you shrink it?
- Explain ZeRO stages 1, 2, 3.
- What is the difference between ZeRO-3 and FSDP?
- How do you shard a 70B model across 8 GPUs?
