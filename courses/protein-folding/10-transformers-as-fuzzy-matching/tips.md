## Going deeper

- **Vaswani et al, 2017** — *Attention Is All You Need* — [https://arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762). The original transformer paper. The three pages of math at the start are worth re-reading every six months.
- **Devlin et al, 2018** — *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding* — [https://arxiv.org/abs/1810.04805](https://arxiv.org/abs/1810.04805). The encoder-only architecture and the MLM training objective that ESM-2 inherits.
- **Chris Hayduk's PLM primer** — Substack series on AlphaFold2, encoder transformers, ESMFold, and ESM3. The core source for this module's "fuzzy matching" framing. Search for *"An idiot's guide to protein language models"* on Substack.
- **Vig et al, 2020** — *BERTology Meets Biology: Interpreting Attention in Protein Language Models* — [https://arxiv.org/abs/2006.15222](https://arxiv.org/abs/2006.15222). Empirical analysis of what individual ESM heads learn — including heads that recover BLOSUM62, secondary structure, and contact patterns.
- **Rao et al, 2021** — *Transformer protein language models are unsupervised structure learners* — [https://www.biorxiv.org/content/10.1101/2020.12.15.422761](https://www.biorxiv.org/content/10.1101/2020.12.15.422761). Shows that the attention maps of a pretrained PLM contain enough signal to recover residue-residue contacts without any supervised structural training.
- **3Blue1Brown's transformer videos** — [https://www.3blue1brown.com/topics/neural-networks](https://www.3blue1brown.com/topics/neural-networks). Visual, geometric explanations of attention. Useful for shoring up the linear-algebra intuition.
- **Karpathy's "Let's build GPT from scratch"** — [https://www.youtube.com/watch?v=kCc8FmEb1nY](https://www.youtube.com/watch?v=kCc8FmEb1nY). Build a working transformer in ~150 lines of PyTorch. The pedagogical North Star.
- **Anthropic / Olah et al on transformer circuits** — [https://transformer-circuits.pub/](https://transformer-circuits.pub/). Treats the FFN layers as sparse key-value memory and shows specific, interpretable "circuits" that emerge in trained models.

## Common confusions

### "Why is the attention pattern not just BLOSUM62?"

It *is*, in a generalised sense — for some heads at some layers. But
the model also learns *contextual* substitution scores: in the middle
of a hydrophobic core, `L` and `I` are extremely similar; on the
surface of a coiled coil, the same pair is far less interchangeable.
Attention's similarity function is conditioned on the embedding
context, so it can express patterns that a fixed substitution matrix
cannot.

### "Where does the database actually live?"

In the weights $\mathbf{W}^Q, \mathbf{W}^K, \mathbf{W}^V$ of every
attention layer, the FFN matrices, and the input embedding matrix
itself. None of these are "lookup tables" in any explicit sense —
they're learned linear projections. The compressed-database analogy
is *functional*, not *architectural*: behaviourally the model retrieves
patterns; mechanically it just multiplies matrices.

### "What does an attention head 'specialise in'?"

Empirically: anywhere from "look at residues 4 ahead in the chain"
(local helix) to "look at far-away residues with similar embeddings"
(distant contacts) to "look at the <CLS> token" (whole-sequence
summary). Multi-head attention provides the dimensionality for
specialisation; SGD gives the gradient signal.

### "Is attention causal?"

In ESM-2 and other encoder-only PLMs, **no** — attention is
bidirectional. Every position can attend to every other position. In
GPT-style decoder models, attention *is* causal (masked to look only
at past positions). Mixing the two regimes leads to encoder-decoder
models like the original transformer; we won't use them in this
course.

## Things to think about before module 11

Before running ESM-2 on a real masked sequence:

1. If a transformer's weights are a compressed database, what kinds
   of *training data* do you expect would systematically improve the
   model's predictions on, say, antibody sequences? On membrane
   proteins? On extremely conserved bacterial enzymes?
2. The MLM objective masks ~15 % of input tokens. Why 15 %, do you
   think? What would happen at 1 %, 50 %, 99 %?
3. The compressed-database analogy predicts that ESMFold should fail
   gracefully — degraded but not catastrophically — on proteins from
   undersampled families. The classical AlphaFold2 pipeline would
   fail abruptly when the MSA is too thin to bootstrap from. Which
   prediction would you bet on a priori?

Next module: actual ESM-2 in PyTorch, masking a residue, and
watching the model fill in the gap.
