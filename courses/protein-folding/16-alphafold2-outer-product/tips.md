## Going deeper

- **Jumper et al, 2021** — *Highly accurate protein structure prediction with AlphaFold* — [https://www.nature.com/articles/s41586-021-03819-2](https://www.nature.com/articles/s41586-021-03819-2). Specifically supplementary Algorithm 10: the outer product mean pseudocode. Worth reading line-by-line.
- **Hayduk's PLM primer Part I** — covers the OPM in compact narrative form. The "consistent co-variation patterns survive averaging" intuition is paraphrased from there.
- **Morcos et al, 2011** — *Direct-coupling analysis of residue coevolution captures native contacts across many protein families* — [https://www.pnas.org/doi/10.1073/pnas.1111471108](https://www.pnas.org/doi/10.1073/pnas.1111471108). The DCA paper. Reads as a clean statistical-physics derivation that motivated everything that came after.
- **Marks et al, 2011** — *Protein 3D Structure Computed from Evolutionary Sequence Variation* — [https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0028766](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0028766). Companion paper to Morcos. Established that DCA contacts are accurate enough to fold proteins. The conceptual ancestor of AlphaFold2.
- **OpenFold** — [https://github.com/aqlaboratory/openfold](https://github.com/aqlaboratory/openfold). Their `outer_product_mean.py` is a clean reference PyTorch implementation.
- **Ovchinnikov & Baker, 2017** — *Why does deep learning work for protein structure prediction?* — [https://www.cell.com/current-opinion-in-structural-biology/abstract/S0959-440X(17)30084-2](https://www.cell.com/current-opinion-in-structural-biology/abstract/S0959-440X\(17\)30084-2). A thoughtful retrospective on the DCA-to-deep-learning transition by two of the field's founders.

## Common confusions

### "What does 'consistent co-variation patterns survive averaging' actually mean?"

A toy example. Suppose 1000 sequences, columns $i$ and $j$. In 500
sequences both columns are `K`; in 500 sequences both are `R`. The
outer products $\mathbf{a}_{k,i} \otimes \mathbf{b}_{k,j}$ for the
two groups point in two specific directions in the $c' \times c'$
matrix space.

If we average all 1000 outer products, the result is a sum of two
"averaged groups" — each direction is preserved with weight 0.5 (its
fraction). The pattern survives.

Now consider columns where there's no co-variation: 250 each of (`K`,
`R`), (`R`, `K`), (`K`, `K`), (`R`, `R`). The four directions in
matrix space are roughly orthogonal; their average is much closer to
zero than any individual outer product. The pattern washes out.

This is what the network exploits. Co-variation = signal that
survives averaging; independence = signal that washes out.

### "Couldn't we just use a single MLP with $\mathbf{a}_{k,i}$ and
$\mathbf{b}_{k,j}$ concatenated?"

You could. Concatenation + MLP and outer product + linear are both
expressive enough to learn arbitrary functions of the pair
$(\mathbf{a}, \mathbf{b})$. The empirical advantage of the outer
product is the **multiplicative** interaction — concatenation only
gives you additive interactions, while outer product gives you
products of components, which capture XOR-like co-variation patterns
more efficiently.

This is the same reason multiplicative gating in attention is more
expressive than additive bias terms.

### "Where does the gap symbol fit in?"

Real MSAs are full of gap columns. AlphaFold2 treats `-` as a 21st
"residue" with its own embedding row. Its embeddings are like any
other amino acid; gradients flow through them. Empirically, the model
learns specific embeddings for gap columns that encode "this position
isn't there" — leading to OPM contributions that effectively encode
"these two columns are gappy in similar sequences" (a useful signal
for structural alignment).

### "Why divide by $S$? What if $S$ varies between batches?"

The mean ensures the OPM output's magnitude is independent of MSA
depth. If you used a sum, deep MSAs would produce $S$-times-larger
updates than shallow ones, leading to learning instability.

In practice, the *effective* $S$ is fixed in AlphaFold2 (uniform
sub-sampling to 512 sequences per training step). The mean is still
the right normalisation regardless.

### "Doesn't this mean OPM produces zero on a single-sequence input?"

Almost. With $S = 1$, the mean is just one outer product
$\mathbf{a}_{1,i} \otimes \mathbf{b}_{1,j}$, projected to pair channels.
That's a deterministic bilinear function of the single sequence's
embeddings — not zero, but much weaker than what you'd get from a
deep MSA.

This is part of why AlphaFold2 underperforms on shallow-MSA proteins:
when $S$ is small, OPM contributes much less informative pair updates,
and the network has to lean harder on row attention's pair bias plus
the triangle updates. ESMFold's solution (module 17) is to skip the
MSA path entirely and use a different mechanism.

## Things to think about before module 17

The set-up for ESMFold:

1. **Question:** if the OPM extracts co-evolutionary signal from
   explicit MSA columns, where would that signal come from in a
   single-sequence model?
2. **Hypothesis (Hayduk Part III):** ESM-2's pretrained weights have
   *implicitly* learned the same co-evolution signal during MLM
   training over hundreds of millions of sequences. Per-residue
   embeddings carry "what an MSA-derived feature would say about this
   position".
3. **Architectural consequence:** ESMFold replaces the entire MSA +
   Evoformer pipeline with ESM-2 + a small structure module. No MSA
   search at inference, no Evoformer's row/column attention, no OPM.

Module 17 develops this story: the trade-offs (speed vs accuracy),
the regimes where each wins (deep-MSA vs shallow-MSA proteins), and
what the future direction looks like.
