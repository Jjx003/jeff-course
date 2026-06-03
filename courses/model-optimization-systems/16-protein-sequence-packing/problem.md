# Protein sequence packing

Protein sequences have wildly different lengths. A batch might contain a
36-residue peptide, a 210-residue enzyme domain, a 760-residue multidomain
protein, and a 1,000-residue repeat protein. If the batch is padded to its
longest sequence, the short proteins spend most of the forward pass pretending
to be padding.

In this lab you will implement **first-fit decreasing** sequence packing. The
setting is intentionally narrow: independent protein sequences going through a
protein-language-model-style workload where masks can prevent cross-sequence
attention. That is the safe case. The broader lesson is how to quantify padding
waste before reaching for heavier optimization.

## The batching problem

For a static batch of size $B$ with sequence lengths $L_1, \ldots, L_B$, a naive
padded representation uses:

$$
B \max_i L_i
$$

token slots. The useful work is:

$$
\sum_i L_i
$$

The waste is:

$$
B \max_i L_i - \sum_i L_i
$$

If one long sequence appears in a batch with several short sequences, the waste
can be severe.

## Packing intuition

Instead of representing each protein as its own padded row, a packing system can
place several short proteins into one fixed-capacity pack:

```text
pack capacity: 1024 tokens

[ protein A: 420 ][ protein B: 310 ][ protein C: 180 ][ padding: 114 ]
```

The model must receive boundary and attention-mask information so residues from
different proteins do not communicate. If that masking is correct, padding slots
are replaced by real residues, improving utilization.

## Algorithm to implement

Implement **first-fit decreasing**:

1. Sort sequences by length from longest to shortest.
2. Place each sequence into the first existing pack with enough remaining
   capacity.
3. If no pack fits, start a new pack.
4. Print the naive padded-token count for batch size 4.
5. Print the packed bins and packed-token count.
6. Print the waste reduction percentage.

First-fit decreasing is greedy. It does not always find the globally optimal
packing, but it is simple, fast, and often effective.

## Why this matters for protein models

For PLM embedding or sequence-level scoring, sequence packing can increase GPU
utilization dramatically. It is especially useful when you process many short
proteins or peptides together with a few longer chains.

For folding or complex prediction, be more careful:

- pair representations may create residue-pair features across packed examples,
- chain boundaries may have biological meaning,
- templates and MSAs are tied to individual targets,
- all-atom geometry modules may assume one coherent molecular system,
- ligand and nucleic-acid inputs make "just pack tokens" unsafe.

This lab uses the clean PLM-style version because it isolates the systems idea.
The caveats are part of the lesson.

## Output contract

Use the data and formatting in the starter file. Do not change the scenario list
or print extra debug lines. The expected output checks the final text.
