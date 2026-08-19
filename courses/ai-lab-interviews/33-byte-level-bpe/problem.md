# Byte-Level BPE

"Implement BPE" is a genuine ML coding prompt, and it is a good one: no framework, no GPU, and the algorithm is simple enough to finish in the time available while being fiddly enough to reveal whether you understand it.

This is also CS336's assignment 1, which makes it worth doing properly.

## What to implement

1. `train_bpe` — count adjacent pairs, merge the most frequent, repeat.
2. `merge_word` — replace every occurrence of a pair with a new id.
3. `encode` — apply merges to new text in the order they were learned.
4. `decode` — concatenate byte strings and decode UTF-8.

Standard library only.

## What the script verifies

- Pre-tokenization keeps leading spaces attached and splits contractions.
- Training starts from all 256 byte values and produces the requested vocabulary size.
- Encoding round-trips exactly for training text **and for text containing accented characters, an emoji, and a fake special token** — the point being that byte-level tokenization has no out-of-vocabulary case and cannot have one.
- Merge order matters: encoding with half the merges gives a different (never shorter) result.
- Compression improves monotonically with vocabulary size, with diminishing returns.
- Words tokenize into fewer tokens than they have characters — which is the whole explanation for why models cannot count letters.

## The detail people get wrong

In `encode`, apply the **earliest-learned** applicable merge, not the first one found scanning left to right.

BPE encoding is defined by merge *order*. Applying merges greedily by position gives a different, and wrong, segmentation — one that will not match how the model was trained. A tokenizer that encodes differently from the one used in pretraining silently degrades everything downstream.

## The bar

Thirty minutes. If you finish early, the interviewer will ask you to make training faster — see the tips for what they are looking for.
