## Why PLL works (when it shouldn't)

For an autoregressive language model (decoder-only, like GPT), the
joint distribution factorises exactly:

$$p(x) = \prod_{i=1}^{L} p(x_i \mid x_{<i}).$$

Summing the log-probabilities gives the true log-likelihood. For
masked language models (encoder-only, like ESM-2 / BERT) there's
no such factorisation. The "pseudo-log-likelihood" expression

$$\text{PLL}(x) = \sum_i \log p(x_i \mid x_{\setminus i})$$

double-counts pairwise dependencies and isn't a normalised
distribution. But — and this is the empirical observation — it
**ranks sequences correctly** for many practical tasks.

Why? Two intuitions:

1. **The conditional is informative.** When the model evaluates
   "what residue is most likely at position $i$, given everything
   else", it's doing the right computation locally. Even if the
   joint normalisation is broken, the local conditional is honest.
2. **Differences are robust.** When you compare WT and a mutant,
   most of the per-position log-probabilities cancel — only the
   masked position(s) at the mutation site change substantially.
   So $\Delta\text{PLL}$ is mostly a sum of $O(\text{number of
   mutations})$ informative terms, not a noisy sum of $O(L)$.

Theoretical work by Wang & Cho (2019) and others has shown that PLL
under a perfect MLM converges to the true log-likelihood under
mild assumptions. In practice, the approximation is close enough
for variant-effect prediction.

## ESM-2's logit head and softmax

ESM-2's forward pass returns, for each token position $i$, a vector
of logits $\ell_{i, a} \in \mathbb{R}^{|V|}$ over the vocabulary
$V$ (33 entries: 25 amino acids + standard tokens + special tokens).

The probability of a specific amino acid $a$ at position $i$ is the
softmax:

$$p(x_i = a \mid x_{\setminus i}) = \frac{\exp(\ell_{i, a})}{\sum_{a' \in V} \exp(\ell_{i, a'})}.$$

For PLL we only need the log-probability of the correct residue, so
the cleaner expression is:

$$\log p(x_i = a^* \mid x_{\setminus i}) = \ell_{i, a^*} - \log \sum_{a' \in V} \exp(\ell_{i, a'}).$$

PyTorch's `F.log_softmax(logits, dim=-1)` computes exactly this
form, and is numerically more stable than naively softmax + log.

### Restricting the softmax to amino acids

ESM-2's vocabulary contains 25 standard amino acid tokens (the 20
canonical AAs plus B, Z, X, U, O for ambiguous codes), plus
`<cls>`, `<pad>`, `<eos>`, `<unk>`, `<mask>`, and a few extras. For
PLL on a "well-behaved" sequence with only the 20 canonical AAs,
the model rarely puts probability on the special tokens — but it
still puts some, which subtly distorts the PLL.

Two implementation choices:

1. **Use the full vocabulary log-softmax.** Most common; matches the
   formal definition. Slight bias from the special-token
   probability mass, but consistent across sequences.
2. **Restrict the softmax to the 20 canonical AAs.** Re-normalise
   over only the AA logits. Slightly cleaner conceptually, but
   makes the metric not directly comparable to other PLL papers.

Our exercise uses option 1 (full vocabulary) — it matches the
standard definition and the slight bias cancels in $\Delta\text{PLL}$.

## What ESM-2 has implicitly learned

ESM-2 trained on UniRef50 (~50 M protein sequences). For our
myoglobin fragment, the model has seen:

- Hundreds of thousands of globin sequences (myoglobin, hemoglobin
  alpha/beta/gamma/delta/epsilon, leghemoglobin, neuroglobin,
  cytoglobin, ...) across all sequenced organisms.
- Co-occurrences and co-variations across all those sequences (the
  same signal Evoformer learns explicitly via OPM, see module 16).
- Local sequence motifs that recur in helix-helix interfaces, in
  heme-binding pockets, in disordered linkers, etc.

When you mask `W15` and ask ESM-2 for the most likely residue, the
model returns:

1. `W` itself (probability ~0.6+) — directly seen in the training set.
2. Other aromatic residues (Y, F) — seen as substitutes.
3. Some hydrophobic non-aromatics (L, M) — occasionally tolerated.
4. Polar / charged residues — very rarely; model rejects these.

The information that "tryptophan at this position is highly
conserved" is not in any explicit knowledge base ESM-2 was given.
It's compressed into the weights of the transformer, available for
retrieval at inference time. This is the "compressed-database"
view from module 10.

## PLL as a fitness proxy

Hopf et al, 2017 (EVmutation) demonstrated that statistical-energy
models trained on MSAs predict deep-mutational-scanning fitness
values with Spearman correlations in the 0.4-0.8 range. Riesselman
et al, 2018 (DeepSequence) extended this with VAEs. Meier et al,
2021 (the ESM-1v paper) showed that ESM-1v PLLs do roughly as well
as DeepSequence on many DMS datasets, **without any per-protein
fine-tuning**.

Concrete numbers from Meier et al 2021 across 41 DMS datasets:

- ESM-1v zero-shot: median Spearman ~0.43.
- DeepSequence (per-protein): median Spearman ~0.40.
- ESM-1b (older, smaller): median Spearman ~0.30.

Cradle's "logiter" (module 22) takes this further: starting from
ESM-2's PLL as the prior, fine-tune the model on assay data and use
the post-fine-tuning PLL as the fitness proxy. Spearman shoots up
to 0.6-0.8.

## Failure modes of PLL

Where PLL gets things wrong:

1. **Domain inserts and deletions.** PLL only handles single-point
   mutations cleanly. Insertions / deletions require re-aligning,
   which the basic PLL formula doesn't address.
2. **Epistasis.** PLL of two simultaneous mutations is roughly the
   sum of the individual PLL deltas, but real fitness has
   interaction effects. PLL underestimates strong epistatic
   interactions.
3. **Strong selection regimes.** PLL ranks sequences by "what's
   likely in the training set", not "what's selected for in this
   specific assay". For a thermostability assay, PLL roughly
   tracks; for a substrate-binding assay against a non-natural
   substrate, PLL is uncorrelated with the ground truth.

For Cradle, this last point matters: their predictor head + g-DPO
is exactly the mechanism that re-aligns the model from "sequence
plausibility" to "this specific assay's fitness landscape" (module
22).

## Computational cost

For a sequence of length $L$ on ESM-2 650M:

- One forward pass: ~50-100 ms on a typical GPU (FP16, batch 1).
- Full PLL (one mask per position): $L \times$ that = 1.5-3 s for
  $L = 30$, 50-100 s for $L = 1000$.
- Cost per million-mutation library: ~3 hours of GPU time for
  $L = 30$, ~3 days for $L = 1000$.

Optimisations:

1. **Batch.** Compute multiple masked positions of the same
   sequence in a single batch (memory-permitting).
2. **Cache wild-type.** PLL of any single-mutant differs from WT
   only at the mutation site. Compute WT PLL once and only the
   single mutated-position log-prob per mutant.
3. **Approximate.** Random-subset masking, as discussed in the
   problem.md, trades a small amount of accuracy for a $5-10\times$
   speedup.

For very large library scoring (e.g. 1 M variants), optimisation 2
is essential. For our 4-variant exercise, the naive approach is
fine.
