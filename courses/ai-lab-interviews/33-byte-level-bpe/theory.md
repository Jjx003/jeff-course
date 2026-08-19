# The Algorithm

## Training

```
vocab = {0..255 -> single bytes}
while len(vocab) < target:
    count every adjacent pair across the corpus
    merge the most frequent pair into a new id
    record the merge
```

**Count over unique words, weighted by frequency.** A corpus has far fewer distinct words than tokens, so representing it as a `{word: count}` map and iterating over that turns a pass over billions of tokens into a pass over millions of word types. Doing this is the difference between a tractable implementation and one that never finishes, and mentioning it unprompted is a good signal.

**Determinism on ties.** Two pairs can have identical counts. Whatever rule you use to break the tie must be deterministic, or two training runs on the same corpus produce different tokenizers. Using `max` on the count alone with Python's stable iteration order is one valid choice; sorting by `(count, pair)` is another. What matters is that you noticed.

## Encoding

Apply the recorded merges **in the order they were learned**:

```python
while len(ids) >= 2:
    candidates = [(rank[p], p) for p in adjacent_pairs(ids) if p in rank]
    if not candidates:
        break
    _, pair = min(candidates)          # EARLIEST-learned, not leftmost
    ids = apply(pair)
```

The `min` over merge rank is the crux. A greedy left-to-right scan produces a different segmentation than the training procedure would have, and the model was trained on the training procedure's output. This is the single most common BPE implementation bug.

## Pre-tokenization

Split the text before BPE ever sees it, on a regex that isolates words, numbers, punctuation, and whitespace runs. Merges may never cross these boundaries.

Without it, BPE would happily learn `" the cat"` as a single token. That generalizes badly and floods the vocabulary with near-duplicate multi-word fragments.

Note that most tokens include their **leading** space (`" the"`, not `"the"`). That is why a prompt ending in a trailing space tokenizes differently from one that does not, and why that measurably changes completions — a real and frequently-encountered gotcha.

## Byte-level

Starting from the 256 byte values rather than a character set gives one decisive property: **every possible input encodes.** There is no `<UNK>` token, and there cannot be one.

The script demonstrates this on a string containing accented Latin characters, an emoji, and a fake special-token-looking sequence — none of which appear in the training corpus. All of it round-trips exactly.

The cost is that non-Latin scripts start at a disadvantage: a character that is one byte in English may be three or four in another script, so it begins as three or four tokens and only merges recover it. That is the mechanical origin of the language-cost asymmetry.

# What This Explains

## Character-level failures

The script prints the token counts: `"strawberry"` is 10 characters and about 8 tokens even with a tiny vocabulary; with a real 100k vocabulary it is 2 or 3. The model never sees the letters. Asking it to count them is asking it to recover information that was discarded before the first layer.

This is worth being precise about in an interview, because "the model can't reason about characters" is the wrong diagnosis and "the representation does not contain characters" is the right one.

## Vocabulary size

The compression sweep in the script shows the shape: large early gains, then flattening. Doubling the vocabulary buys steadily less compression while costing linearly more embedding parameters.

The trade in full:

| Larger vocabulary | Smaller vocabulary |
|---|---|
| fewer tokens per document | more tokens per document |
| more text fits in a fixed context | less text fits |
| cheaper per character to train and serve | more expensive per character |
| more embedding parameters | fewer |
| larger, slower softmax | smaller, faster |
| rarer tokens, less-trained embeddings | every token well trained |

The last row is underrated: a 256k vocabulary means many tokens appear rarely in training, so their embeddings are poorly estimated. That is the same mechanism that produces glitch tokens.
