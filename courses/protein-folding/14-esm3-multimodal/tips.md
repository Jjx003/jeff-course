## Going deeper

- **Hayes et al, 2024** — *Simulating 500 million years of evolution with a language model* — [https://www.evolutionaryscale.ai/blog/esm3-release](https://www.evolutionaryscale.ai/blog/esm3-release). The official ESM3 release blog post. Excellent for the high-level story and the esmGFP case study.
- **The ESM3 paper preprint** — [https://www.biorxiv.org/content/10.1101/2024.07.01.600583](https://www.biorxiv.org/content/10.1101/2024.07.01.600583). Full technical details on the structure tokenisation, function vocabulary, training objective, and ablations.
- **van den Oord et al, 2017** — *Neural Discrete Representation Learning* — [https://arxiv.org/abs/1711.00937](https://arxiv.org/abs/1711.00937). The original VQ-VAE paper that ESM3's structure tokeniser builds on.
- **Chang et al, 2022** — *MaskGIT: Masked Generative Image Transformer* — [https://arxiv.org/abs/2202.04200](https://arxiv.org/abs/2202.04200). The iterative-denoising decoding strategy ESM3 uses for generation.
- **AlphaFold3 paper, Abramson et al, 2024** — *Accurate structure prediction of biomolecular interactions with AlphaFold 3* — [https://www.nature.com/articles/s41586-024-07487-w](https://www.nature.com/articles/s41586-024-07487-w). The diffusion-based parallel system. Worth reading alongside ESM3 to compare design choices.
- **Magnus Ross's "Idiot's guide to lead optimisation"** — Magnus Ross blog. Discusses why pure-sequence PLMs are insufficient for serious design work and how multimodal models change the game.
- **Hayduk's PLM primer Part IV** — covers the von Neumann argument and ESM3 in compact form. Highly recommended as a companion read.

## Common confusions

### "Why doesn't a sequence-only PLM see structure too?"

It does, *implicitly*. ESM-2's attention maps recover contact maps
without any structural training (Rao et al, 2021). The catch is that
this implicit signal is bottlenecked by the MLM objective and by the
fact that sequence is a noisy proxy for structure for distantly-related
proteins. A direct structure channel (ESM3) gets you a less lossy path.

### "Is ESM3 better at structure prediction than AlphaFold2?"

Roughly equivalent for typical proteins; ESM3's structure decoder
isn't the focus of the model. For absolute structure-prediction
quality on standard benchmarks, AlphaFold2 / AlphaFold3 are still
the reference. ESM3's strength is **conditional generation** —
controlled design at scale.

### "What does 'multimodal' actually mean here?"

In NLP, "multimodal" usually means *vision + language*. In protein
ML, it means *sequence + structure + function*. The architecture
trick is the same: tokenise everything to a shared vocabulary and
train a single transformer.

### "Why discrete tokens for structure rather than continuous coords?"

Two reasons. First, the entire transformer machinery — softmax over
vocab, cross-entropy loss, top-k decoding — works only on discrete
tokens. Plumbing continuous coords through a categorical-output model
requires extra machinery. Second, discretisation regularises: the
model can't memorise specific atomic positions and instead has to
learn structural classes. This generalises better to novel sequences.

The trade-off, as theory.md notes, is that the structure
representation is necessarily lossy. A second-stage decoder converts
structure tokens back to coordinates with full precision.

### "What's special about the esmGFP demo?"

Two things. First, GFP is a well-studied, easy-to-test target — its
fluorescence is observable in any standard biology lab without
specialised equipment. Second, 58 % identity to the nearest natural
GFP is *far* outside what evolution has produced. The model
extrapolated rather than interpolated, which is hard to do honestly
without overfitting. The wet-lab confirmation makes the
extrapolation real, not just a numerical curiosity.

## Things to think about before module 15

The next two modules go deep on AlphaFold2's Evoformer — the explicit
MSA-based architecture that ESM3 partly emulates. Things worth
thinking about ahead of time:

1. **Where does the MSA come from in AlphaFold2?** What inputs does
   it need at inference time? (Hint: a database search.)
2. **How is the MSA different from a single sequence as a network
   input?** What dimensions does it have, what does each axis mean?
3. **In the multimodal framing of ESM3, an MSA is a kind of "structure
   token" that AlphaFold2 needs explicitly.** Why?

Module 15 introduces the row/column attention pattern; module 16
introduces the outer-product-mean operation that bridges from
sequence space to pair space.
