# Rapid-Fire Answers

**"Explain BPE."**
> Start with a vocabulary of all 256 bytes, repeatedly count adjacent pairs in the corpus, merge the most frequent into a new token, and record the merge. Encoding replays the merges in the order they were learned. Byte-level means no out-of-vocabulary token is possible.

**"Why can't models count letters in a word?"**
> They never see letters. "strawberry" is two or three tokens, so the character-level information is not in the representation. It is a tokenization limitation, not a reasoning one.

**"What does vocabulary size trade off?"**
> Larger vocabulary means fewer tokens per document — cheaper per character, more content per context window — against more embedding parameters and a slower softmax. Compression improves sublinearly, so the returns diminish sharply. Most models sit between 32k and 256k.

**"Walk me through a pretraining data pipeline."**
> Acquire, extract text from HTML, identify language, filter for quality with heuristics plus a learned classifier, deduplicate exactly and then fuzzily with MinHash, decontaminate against eval sets, mix sources at chosen ratios, then tokenize and pack. Deduplication is the highest-leverage single step.

**"How would you detect contamination?"**
> N-gram overlap as a baseline, but it misses paraphrases. Better: temporal holdouts on data created after the cutoff, canary strings, and exchangeability tests — a benchmark's examples are exchangeable, so a contaminated model assigns higher likelihood to the dataset's canonical row ordering than to a shuffled one. Perplexity that is anomalously low relative to comparable unseen text is another signal.

**"Your model scores 85% on MMLU. How much do you believe it?"**
> It depends on whether the benchmark predates the cutoff, whether decontamination was run and its method published, whether a temporal holdout or private variant agrees, and how much the number moves with prompt format. I would want a freshly-authored variant before treating it as a capability claim.

# Traps

- **Calling character-counting failures a reasoning problem.** It is representational.
- **Saying a bigger vocabulary is free** because embeddings are a small fraction of a large model. It is nearly free at 70B and expensive at 700M, and the softmax cost is real at any size.
- **Forgetting pre-tokenization.** Without it BPE learns merges spanning word boundaries.
- **Treating n-gram overlap as sufficient decontamination.** Paraphrases pass through it untouched.
- **Quoting a benchmark score without a prompt format.** Format alone can move scores by 10 points.

# Further Reading

- [Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909) — BPE for NLP.
- [Language Models are Unsupervised Multitask Learners](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf) — byte-level BPE, section 2.2.
- [SolidGoldMagikarp](https://www.lesswrong.com/posts/aPeJE8bSo6rAFoLqg/solidgoldmagikarp-plus-prompt-generation) — glitch tokens, and a genuinely entertaining read.
- [Deduplicating Training Data Makes Language Models Better](https://arxiv.org/abs/2107.06499)
- [The RefinedWeb Dataset](https://arxiv.org/abs/2306.01116) and [Dolma](https://arxiv.org/abs/2402.00159) — two well-documented pipelines.
- [Holistic Evaluation of Language Models](https://arxiv.org/abs/2211.09110) — HELM, on evaluation methodology.
