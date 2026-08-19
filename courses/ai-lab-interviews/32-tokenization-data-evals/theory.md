# Byte-Pair Encoding

## The algorithm

**Training:**

1. Start with a vocabulary of all 256 byte values.
2. Count every adjacent pair in the corpus.
3. Merge the most frequent pair into a new token; record the merge.
4. Repeat until the vocabulary reaches the target size.

**Encoding:** apply the recorded merges to new text, in the order they were learned. The merge order *is* the model — it is what makes encoding deterministic and reproducible.

## Byte-level BPE

Starting from bytes rather than characters, as GPT-2 onwards do, has one decisive property: **no out-of-vocabulary token is possible.** Any byte sequence encodes. That removes the `<UNK>` token entirely and makes the tokenizer robust to any input — emoji, corrupted text, binary-looking data.

The cost is that a non-Latin script may take several bytes per character before merges, so it starts at a disadvantage that merges only partly recover.

## Pre-tokenization

Before BPE runs, text is split by a regex — typically on whitespace and punctuation boundaries. This is not cosmetic. Without it, BPE would learn merges spanning word boundaries, producing tokens like `" the cat"` that generalize badly and explode the vocabulary with near-duplicates.

GPT-2's pattern splits contractions, letters, numbers, punctuation, and whitespace runs. GPT-4's adds digit grouping — which is why its arithmetic behaves differently, and a good detail to know.

## Pathologies, and what they explain

**Character blindness.** "How many r's in strawberry?" is hard because the model sees two or three tokens, not ten letters. It is not a reasoning failure; the information is genuinely not in the representation.

**Number splitting.** `1234` might be one token, or `12`+`34`, or `1`+`234`, depending on frequency in the training corpus. Arithmetic accuracy varies with how numbers happen to split — which is why several models now force digit-by-digit tokenization.

**Language inequity.** English is roughly 4 characters per token. Many other languages are 2 or fewer, so the same content costs 2–4x more tokens: more expensive to serve, and it consumes context faster. This is a real fairness issue, not a curiosity.

**Glitch tokens.** Tokens that appear in the tokenizer's training corpus but almost never in the model's — the `SolidGoldMagikarp` family. Their embeddings are essentially untrained, and prompting with them produces bizarre behavior. The cause is a tokenizer trained on a different corpus from the model.

**Trailing whitespace.** A prompt ending in a space tokenizes differently from one that does not, because most tokens include their leading space. It measurably changes completions and is a real source of "why did my prompt stop working".

## Alternatives

**SentencePiece** treats input as a raw stream including spaces (as `▁`), so it needs no pre-tokenization and detokenizes losslessly — better for languages without whitespace word boundaries.

**Unigram LM** starts with a large vocabulary and prunes it, choosing the segmentation that maximizes likelihood. It supports sampling different segmentations of the same text, which is a useful regularizer.

**Byte-level / tokenizer-free** models (ByT5, MegaByte, and more recent entropy-based patching) remove tokenization entirely. Sequences get much longer, so they need architectural changes to be affordable. This is an active area and a good thing to know exists.

# Data Pipelines

The stage list, roughly in order:

1. **Acquisition** — Common Crawl, code repositories, books, papers, curated sources.
2. **Extraction** — HTML to text. Harder and more consequential than it sounds; extraction quality is a real differentiator between corpora.
3. **Language identification** — usually a fastText classifier.
4. **Quality filtering** — heuristics (line lengths, symbol ratios, stopword presence) plus a learned classifier trained to recognize text resembling a high-quality reference set.
5. **Deduplication** — exact hashing, then fuzzy near-duplicate removal via MinHash/LSH.
6. **Decontamination** — remove anything matching an evaluation set.
7. **Mixing** — sample from sources at chosen ratios, upsampling high-quality domains.
8. **Tokenization and packing** — concatenate into fixed-length sequences with document boundaries respected.

## Deduplication is the single highest-leverage step

Duplicated text causes memorization, wastes compute, and inflates evaluation scores. Removing near-duplicates measurably improves models at fixed token count — one of the most reliably reproduced findings in the field.

MinHash for near-duplicates: shingle each document, hash the shingles, keep the minimum hash per permutation, and bucket by signature bands. Documents sharing a band are candidates for exact comparison.

## Mixing and annealing

Data mixture matters roughly as much as architecture. Code improves reasoning even on non-code tasks. Maths improves reasoning. Multilingual data costs some English performance and buys a lot elsewhere.

**Annealing:** shift the mixture toward high-quality curated sources during the final learning-rate decay phase. This is one of the reasons warmup-stable-decay is convenient — the anneal and the decay happen together.

# Evaluation

## The formats

**Multiple choice** (MMLU, ARC, HellaSwag) — scored by comparing log-likelihoods of the options. Cheap and reproducible; sensitive to normalization choices (per-token versus per-sequence likelihood) in ways that move scores by several points.

**Generative** (GSM8K, HumanEval, MATH) — the model generates and the answer is checked. More realistic and much more sensitive to prompt format, few-shot examples, and parsing.

**Model-graded** (MT-Bench, AlpacaEval, arena-style) — a strong model judges. Scales to open-ended tasks, and inherits the judge's biases — notably a preference for longer responses and for the judge's own outputs.

**Human preference** (Chatbot Arena) — the gold standard for helpfulness, expensive, slow, and subject to its own popularity and presentation effects.

## Contamination

The most important evaluation problem, and the one you are most likely to be asked about.

**Detection methods:**

- **N-gram overlap** between the eval set and the training corpus. The standard check, and the weakest — paraphrases pass straight through.
- **Canaries** — insert unique strings into training data and test whether the model reproduces them.
- **Ordering tests** — a benchmark's examples are exchangeable, so a clean model should be indifferent to the order they appear in. A contaminated model assigns higher log-likelihood to the dataset's canonical example ordering than to a random permutation of its rows. (Note this is about the order of *examples in the dataset*, not the order of answer options within a question — clean models are sensitive to option order too, so that would prove nothing.)
- **Temporal holdouts** — evaluate on data created after the training cutoff. The cleanest signal available.
- **Perplexity gaps** — suspiciously low perplexity on a benchmark relative to similar unseen text.

**What to say when asked "how much do you believe an 85% score?"** — *It depends on whether the benchmark predates the training cutoff, whether the authors ran decontamination and published the method, whether the score is consistent with a temporal holdout or a private variant, and how sensitive the number is to prompt format. I would want a held-out or freshly-authored variant before treating it as a capability claim.*

That answer is the point of this section.

## Other ways to fool yourself

- **Prompt-format sensitivity.** Few-shot ordering and formatting can move scores by 10 points. Always report the format.
- **Metric mismatch.** Exact-match on a free-form answer punishes correct-but-differently-phrased responses.
- **Overfitting to the benchmark** across many iterations of model development — the eval becomes a training signal through you.
- **Aggregate scores hiding regressions.** An average can rise while an important subset falls.
