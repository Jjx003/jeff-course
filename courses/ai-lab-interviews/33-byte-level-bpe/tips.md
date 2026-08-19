# Debugging Guide

**Round-trip fails on non-ASCII.** You are working with `str` where you should be working with `bytes`. Encode to UTF-8 *first*, then merge byte ids.

**Encoding gives a different result from what training would produce.** You applied merges greedily by position instead of by learned rank. Use `min` over the merge index.

**Training is unbearably slow.** You are recounting every pair over the whole corpus after each merge, on the raw token stream. Count over unique words weighted by frequency, and — better — only recount pairs in words that actually contained the merged pair.

**Two training runs give different vocabularies.** Tie-breaking is non-deterministic. Fix a rule and state it.

**Some words tokenize into more tokens than expected.** Check that pre-tokenization is applied consistently in both training and encoding. A mismatch there is invisible until quality drops.

# If You Finish Early

The follow-up is always about speed. What they want to hear:

- **Count over unique words, not the token stream.** The single biggest win.
- **Incremental recounting.** After merging a pair, only words that contained it can have changed counts. Maintain an index from pair to the words containing it and update locally.
- **A priority queue over pair counts**, with lazy deletion, instead of a full `max` scan each round.
- **Parallelism.** Counting is embarrassingly parallel over corpus shards; merging is sequential.
- **The real answer for production:** use a Rust implementation like Hugging Face `tokenizers`. Training a real tokenizer on hundreds of gigabytes is not a Python job.

# Rapid-Fire Answers

**"Explain BPE."**
> Start with a vocabulary of the 256 byte values, repeatedly count adjacent pairs across the corpus, merge the most frequent into a new token, and record the merge. Encoding replays the merges in learned order. Byte-level means no out-of-vocabulary token is possible.

**"Why does encoding apply merges by rank rather than position?"**
> BPE is defined by merge order. A greedy left-to-right scan produces a different segmentation from the training procedure, so a model trained one way and served the other is silently mis-tokenized.

**"Why pre-tokenize?"**
> Otherwise BPE learns merges spanning word boundaries — tokens like `" the cat"` — which generalize badly and fill the vocabulary with near-duplicates. It is also where the convention of attaching leading spaces to tokens comes from.

**"How would you make training fast?"**
> Count over unique words weighted by frequency rather than over the token stream, then recount incrementally — only words containing the merged pair can change. A priority queue with lazy deletion replaces the full max scan. Beyond that, shard and parallelize the counting.

# Further Reading

- [Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909)
- [minbpe](https://github.com/karpathy/minbpe) — a clean, readable reference implementation. Read it after you have written your own, not before.
- [CS336 Assignment 1](https://github.com/stanford-cs336/assignment1-basics) — the same exercise at realistic scale, with a speed requirement.
- [Hugging Face tokenizers](https://github.com/huggingface/tokenizers) — what production actually uses.
