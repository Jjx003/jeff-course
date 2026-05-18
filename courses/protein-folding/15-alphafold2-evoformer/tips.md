## Going deeper

- **Jumper et al, 2021** — *Highly accurate protein structure prediction with AlphaFold* — [https://www.nature.com/articles/s41586-021-03819-2](https://www.nature.com/articles/s41586-021-03819-2). The AlphaFold2 paper. The supplementary information contains every architectural detail; figure 3 of the main text is the canonical Evoformer diagram.
- **AlphaFold2 supplementary, Algorithm 4-7** — the pseudocode for row attention, column attention, MSA transition, and outer product mean is in the supplement and is the cleanest reference for implementing it yourself.
- **The "Illustrated Transformer" extended for AlphaFold2 — Borgeaud's lectures** — [https://www.youtube.com/watch?v=B5_AKWAJlLM](https://www.youtube.com/watch?v=B5_AKWAJlLM). DeepMind's own walkthrough of the architecture.
- **Hayduk's PLM primer Part I** — covers the Evoformer in compact form. Direct source for this module's framing.
- **OpenFold** — [https://github.com/aqlaboratory/openfold](https://github.com/aqlaboratory/openfold). An open-source PyTorch reimplementation of AlphaFold2. Reading the `evoformer.py` file is the best way to understand the architecture if pseudocode isn't enough.
- **ColabFold** — [https://colab.research.google.com/github/sokrypton/ColabFold/blob/main/AlphaFold2.ipynb](https://colab.research.google.com/github/sokrypton/ColabFold/blob/main/AlphaFold2.ipynb). Run AlphaFold2 in the browser via Google Colab. Useful for getting a feel for inputs, outputs, and runtimes.

## Common confusions

### "Why two attention axes? Couldn't we just flatten?"

You could flatten $\mathbf{m}$ to a $(SL, c_m)$ tensor and run regular
attention, but the cost would be $O((SL)^2 c_h) = O(S^2 L^2 c_h)$ —
$L$ times more expensive than column attention and $S$ times more
expensive than row attention. The factored form is much cheaper and
also encodes a useful structural prior: along-the-sequence patterns
and across-sequences patterns are different in nature, and giving
them their own attention layers is more parameter-efficient.

### "Where does co-evolution actually appear?"

It enters via column attention and the outer product mean.

- **Column attention** — at column $i$, the attention from sequence
  $k$ to sequence $k'$ depends on how similar their residues at
  column $i$ are. Sequences with the same residue at $i$ get high
  cross-attention; conserved columns produce coherent updates.
- **Outer product mean** (module 16) — projects pairs of MSA columns
  into the pair representation. If columns $i$ and $j$ co-vary, the
  outer products' mean acquires a recognizable signature.

Together these two operations let the network *use* the MSA's
co-evolutionary signal at every Evoformer block.

### "What's the role of the pair representation if the structure module reads it?"

The pair representation $\mathbf{z}_{ij}$ is approximately a
distance / orientation feature for residue pair $(i, j)$. It's the
intermediate "language" the network uses to communicate structural
hypotheses between layers and to the final structure module. Think of
it as the network's internal contact map / distance map.

### "Is row attention 'across the MSA' or 'within a sequence'?"

**Within a sequence**, in the same way as a vanilla transformer's
self-attention. Each row of the MSA is one sequence; row attention
operates within that sequence over its $L$ residue positions. The
"row" in the name refers to the row of the MSA matrix; the operation
itself is exactly the kind of attention you'd run on a single
sequence.

### "Can I run the Evoformer alone, without the structure module?"

Yes — and people do. The Evoformer's outputs $\mathbf{s}$ and
$\mathbf{z}$ are useful for many tasks: contact-map prediction,
distance prediction, function-aware embeddings. AlphaFold2's pair
representation has been re-used in dozens of subsequent papers as a
"pretrained" feature.

## Things to think about before module 16

Module 16 introduces the **outer product mean** — the operation
that lets the MSA representation update the pair representation.
A few preview questions:

1. The outer product of two vectors $\mathbf{a} \in \mathbb{R}^{c'}$
   and $\mathbf{b} \in \mathbb{R}^{c'}$ is a matrix $\mathbf{a} \mathbf{b}^\top \in \mathbb{R}^{c' \times c'}$. Why might this be a
   good way to encode "the relationship between two columns"?
2. If you take an outer product for every sequence in the MSA and
   *average* across sequences, what kind of signal survives the
   averaging and what kind washes out?
3. The pair representation has $c_z$ channels. The outer product
   produces $(c')^2$ entries. How do they connect? (Hint: a final
   linear projection.)

Hold these in mind for module 16.
