# Study hints

## Before starting

Take two minutes to classify the main course ideas by phase:

- prefill,
- decode,
- serving scheduling,
- memory management,
- fine-tuning,
- protein embedding,
- structure prediction,
- biological screening.

Most quiz mistakes come from putting an optimization in the wrong phase.

## During the quiz

- Read the noun carefully: attention matrix, cache, batch, draft, sequence,
  pair representation, ligand, affinity.
- Look for the resource being saved: HBM traffic, cache memory, wall-clock
  latency, padding, or expensive biological evaluation.
- For formulas, check whether the expression is linear in sequence length,
  quadratic in sequence length, or tied to draft-prefix acceptance.
- For biology questions, separate "structure confidence" from "binding
  affinity" and "monomer accuracy" from "interface accuracy."

## After finishing

For each missed question, write a one-sentence correction in this form:

```text
I confused <optimization> with <different optimization>; the actual bottleneck was <resource/phase>.
```

That small habit turns quiz feedback into a durable systems map.
