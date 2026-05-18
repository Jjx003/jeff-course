## The masked-language-model objective

ESM-2's training objective is exactly the one BERT introduced for
English text. Given a sequence $\mathbf{x} = (x_1, \dots, x_L)$ and a
random subset $\mathcal{M} \subset \{1, \dots, L\}$ of "masked"
positions, the model is asked to maximise

$$\mathcal{L}_{\text{MLM}}(\theta) = \sum_{i \in \mathcal{M}} \log p_\theta\!\left(x_i \,\big|\, \mathbf{x}_{\setminus i}\right)$$

where $\mathbf{x}_{\setminus i}$ is the sequence with position $i$
replaced by `<mask>`. ESM-2 follows BERT in masking ~15 % of positions.
Of those:

- 80 % are replaced with `<mask>`.
- 10 % are replaced with a random other amino acid.
- 10 % are left unchanged.

The mixed strategy (versus 100 % `<mask>`) prevents the model from
learning that `<mask>` is a special signal it should rely on; it has
to be ready to predict any position from its context regardless of
whether the input has been corrupted.

## Why does MLM training implicitly learn co-evolution?

This is the key insight that makes ESMFold (module 17) work.

Consider the training data: hundreds of millions of UniRef sequences,
many of which are homologous (overlapping with each other across
families). When the model masks position $i$ in a globin sequence, the
training signal asks "what's the most likely letter here, given
positions $1, \dots, i-1, i+1, \dots, L$?".

The answer depends on the rest of the sequence. If position $i$
co-evolves with position $j$ — i.e. across the globin family,
mutations at $i$ tend to come paired with compensating mutations at
$j$ — then the model has to attend to position $j$ when predicting
position $i$.

After billions of gradient steps over millions of sequences,
**attention heads emerge that recover the same co-evolutionary signal
an explicit MSA would give you**. This was empirically verified in
Rao et al, 2021 — the attention maps of pretrained ESM-1 alone are
enough to predict residue-residue contacts at MSA-comparable accuracy.

The model never saw an MSA at training time. The signal is an emergent
consequence of the MLM objective on a homology-rich corpus.

## Pseudo-perplexity as a sanity check

One way to evaluate "how well does this model fit a sequence" without
training labels: compute the **pseudo-log-likelihood (PLL)**

$$\text{PLL}(\mathbf{x}) = \sum_{i=1}^{L} \log p_\theta\!\left(x_i \,\big|\, \mathbf{x}_{\setminus i}\right)$$

by masking each position one at a time and summing the log-probability
of the original residue. PLL is a powerful zero-shot scoring function
for variant effects (modules 20, 22).

Note that PLL is *not* the proper likelihood $\log p(\mathbf{x})$ —
that would require autoregressive factorisation, which BERT-style
models don't expose. But PLL correlates strongly with proper
likelihood and is widely used.

## Top-1 accuracy and the "trivial mask" trap

A trick for understanding ESM-2's behaviour: if you mask a position
that has a UNIQUE most-likely letter given context — say, a conserved
catalytic histidine — the model tends to top-1 the correct letter
with very high probability. If you mask a position that's evolutionary
free (a surface loop), the top-5 distribution is much flatter and
top-1 accuracy is lower.

A common mistake when first using ESM-2 is to evaluate "top-1
accuracy" on uniformly-random positions and conclude the model is
"only" 50–60 % accurate. The 50–60 % comes from averaging over
high-entropy and low-entropy positions; conditioned on conserved
positions the model is much sharper.

For a serious evaluation, compute PLL and compare it across known
wild-type vs known destabilising mutants. Module 20 walks through
exactly this.

## ESM-2's logit head

After the transformer stack produces an $(L+2, d)$ representation,
ESM-2 has a small **language-model head** on top:

$$\text{logits}_i = \mathbf{W}_{\text{LM}}\, \text{LayerNorm}(\mathbf{h}_i) + \mathbf{b}_{\text{LM}}$$

where $\mathbf{h}_i$ is the final-layer hidden state at position $i$
and $\mathbf{W}_{\text{LM}} \in \mathbb{R}^{V \times d}$. The logits
have one entry per token in the alphabet (33 entries for ESM-2). Take
softmax along the vocabulary dimension to get a probability
distribution over tokens.

In HuggingFace `transformers`, the wrapper class
`EsmForMaskedLM` exposes this head automatically — calling the model
returns an object with `.logits` of shape `(batch, seq_len, vocab)`.

When you index the top-5 predictions, you'll usually want to filter
out non-amino-acid tokens (`<mask>`, `<pad>`, `<cls>`, `<eos>`,
ambiguity codes) — the model technically *can* predict these but
they're never useful as "residue substitution suggestions".

## Indexing into the tokenizer

The HuggingFace tokenizer exposes the same vocabulary information
that `fair-esm`'s `Alphabet` does, just with different attribute
names:

```python
tokenizer.cls_token_id        # int, <cls>
tokenizer.pad_token_id        # int, <pad>
tokenizer.eos_token_id        # int, <eos>
tokenizer.mask_token_id       # int, <mask>
tokenizer.convert_tokens_to_ids("M")   # int, the M residue's id
```

To filter top-5 predictions to amino-acid letters only:

```python
AA_LETTERS = "ACDEFGHIKLMNPQRSTVWY"
aa_token_ids = torch.tensor(
    [tokenizer.convert_tokens_to_ids(aa) for aa in AA_LETTERS]
)
aa_logits = position_logits[aa_token_ids]
aa_probs = torch.softmax(aa_logits, dim=-1)
```

Then `aa_probs` is a probability vector over the 20 amino acids only.
Strictly speaking this is *not* the same as taking softmax over the
full 33-token vocab and slicing — the latter loses some probability
mass to the `<mask>`, ambiguity, and special tokens. In practice the
model concentrates almost all probability on amino-acid tokens
anyway, so the two approaches agree to ~3 decimal places.

## Memory and speed

For a 30-residue sequence on ESM-2 650M:

- **Weights:** ~2.6 GB (FP32) or ~1.3 GB (FP16).
- **Activations:** small enough to fit easily on a 6 GB GPU.
- **Inference time:** sub-second on GPU, ~5–15 seconds on CPU.

For longer sequences, memory grows roughly linearly until you hit the
$O(L^2)$ attention bottleneck. At $L \approx 1024$, ESM-2 650M starts
needing more careful memory management; at $L \approx 4096$, you'll
need either chunked attention, gradient checkpointing, or a smaller
checkpoint.

## What does a "load failure" look like?

Common errors when running this module:

- **Out of memory** on the GPU: load with
  `EsmForMaskedLM.from_pretrained(..., torch_dtype=torch.float16)` to
  halve the weight footprint, or fall back to `cpu`.
- **`transformers` not installed**: `requirements.txt` pins it; the
  platform's UV-based runner installs it automatically.
- **`torch` mismatch with CUDA driver**: install the right PyTorch
  build for your CUDA version from [https://pytorch.org/get-started/](https://pytorch.org/get-started/).
- **Slow first run**: HuggingFace downloads the weights from the Hub
  on first use (~2.6 GB). Subsequent runs reuse the cached file in
  `~/.cache/huggingface/hub/`.
