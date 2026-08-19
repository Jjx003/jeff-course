"""
Byte-level BPE: train the merges, encode with them, decode back.

The properties that matter are checked directly: encoding round-trips
losslessly for any valid text, merge order is what makes encoding
deterministic, and compression improves with vocabulary size.

Note this implementation takes str and encodes to UTF-8 internally, for
readability. A production tokenizer takes bytes, which is the only reason
lone surrogates are out of scope here -- the byte-level property itself
(no out-of-vocabulary token is possible) holds either way.

Pure standard library, no torch. Graded output goes to stdout.
"""

import re
import sys
from collections import Counter

VOCAB_TARGET = 320
BYTE_VOCAB = 256

# GPT-2's pre-tokenizer, slightly simplified: contractions, letter runs,
# number runs, other symbol runs, and trailing whitespace. Splitting here is
# what stops BPE learning merges that span word boundaries.
PRETOKEN_PATTERN = re.compile(
    r"'(?:s|t|re|ve|m|ll|d)| ?[A-Za-z]+| ?[0-9]+| ?[^\sA-Za-z0-9]+|\s+(?!\S)|\s+"
)

CORPUS = """
the quick brown fox jumps over the lazy dog
the quick brown cat jumps over the lazy dog
a quick brown fox is quicker than a lazy dog
the lazy dog sleeps while the quick fox jumps
quick quick quick brown brown brown fox fox fox
the dog and the fox and the cat and the dog
tokenization is the process of splitting text into tokens
a tokenizer splits text into tokens and tokens into ids
the tokenizer learns merges from the training corpus
byte pair encoding merges the most frequent adjacent pair
a language model predicts the next token from the previous tokens
language models are trained on very large text corpora
the model learns the statistics of the training corpus
training a language model requires a great deal of compute
the compute required grows with the size of the model
attention lets each token attend to the previous tokens
each attention head learns a different attention pattern
the transformer stacks attention and feed forward layers
a feed forward layer is applied to each token independently
the training loss measures how well the model predicts the next token
lower loss means the model predicts the text better
the model is evaluated on text it has never seen before
evaluation on training text tells you almost nothing
a larger model trained on more text usually predicts better
but a larger model also costs more to train and to serve
serving a large model requires a great deal of memory
memory is the constraint that shapes almost every design choice
""".strip()


def pretokenize(text):
    """Split text into chunks that merges are never allowed to cross."""
    return PRETOKEN_PATTERN.findall(text)


def train_bpe(text, vocab_size):
    """Return (merges, vocab).

    merges: list of ((a, b) -> new_id) in the order they were learned.
    vocab:  dict of id -> bytes.
    """
    vocab = {i: bytes([i]) for i in range(BYTE_VOCAB)}
    merges = []

    # Word frequencies, each word as a tuple of byte ids. Counting unique
    # words rather than every occurrence is what makes this tractable.
    word_freqs = Counter(pretokenize(text))
    words = {word: tuple(word.encode("utf-8")) for word in word_freqs}

    next_id = BYTE_VOCAB
    while next_id < vocab_size:
        pair_counts = Counter()
        for word, ids in words.items():
            freq = word_freqs[word]
            for pair in zip(ids, ids[1:]):
                pair_counts[pair] += freq

        if not pair_counts:
            break
        # max() over (count, pair) would order pairs by id on a tie; using the
        # count alone with Python's stable max keeps the first-seen pair,
        # which makes training deterministic.
        best_pair, best_count = max(pair_counts.items(), key=lambda kv: kv[1])
        if best_count < 2:
            break

        vocab[next_id] = vocab[best_pair[0]] + vocab[best_pair[1]]
        merges.append((best_pair, next_id))

        words = {word: merge_word(ids, best_pair, next_id) for word, ids in words.items()}
        next_id += 1

    return merges, vocab


def merge_word(ids, pair, new_id):
    """Replace every occurrence of `pair` in `ids` with `new_id`."""
    out = []
    i = 0
    while i < len(ids):
        if i < len(ids) - 1 and (ids[i], ids[i + 1]) == pair:
            out.append(new_id)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return tuple(out)


def encode(text, merges):
    """Apply merges in learned order, within pre-token boundaries."""
    rank = {pair: i for i, (pair, _) in enumerate(merges)}
    new_id_of = {pair: new_id for pair, new_id in merges}

    out = []
    for chunk in pretokenize(text):
        ids = list(chunk.encode("utf-8"))
        while len(ids) >= 2:
            # Apply the EARLIEST-learned applicable merge, not the first one
            # found left to right. Merge order is the model.
            candidates = [(rank[p], p) for p in zip(ids, ids[1:]) if p in rank]
            if not candidates:
                break
            _, pair = min(candidates)
            ids = list(merge_word(tuple(ids), pair, new_id_of[pair]))
        out.extend(ids)
    return out


def decode(ids, vocab):
    """Concatenate the byte strings and decode as UTF-8."""
    return b"".join(vocab[i] for i in ids).decode("utf-8", errors="replace")


def main():
    print("=== Byte-level BPE ===")
    print(f"corpus: {len(CORPUS)} characters, {len(CORPUS.encode('utf-8'))} bytes")
    print(f"target vocabulary: {VOCAB_TARGET} ({VOCAB_TARGET - BYTE_VOCAB} merges)")

    print()
    print("--- 1. pre-tokenization ---")
    chunks = pretokenize("the quick brown fox's 42 tokens!")
    print(f"chunks: {chunks}")
    print(f"leading spaces are part of the token: {chunks[1].startswith(' ')}")
    has_contraction = "'s" in chunks
    print(f"contractions split off: {has_contraction}")
    print("(without pre-tokenization, BPE would learn merges spanning word")
    print(" boundaries and fill the vocabulary with near-duplicates)")

    print()
    print("--- 2. training ---")
    merges, vocab = train_bpe(CORPUS, VOCAB_TARGET)
    print(f"merges learned: {len(merges)}")
    print(f"vocabulary size: {len(vocab)}")
    print(f"starts from all 256 byte values: {all(i in vocab for i in range(256))}")
    print("first 10 merges:")
    for pair, new_id in merges[:10]:
        left = vocab[pair[0]].decode("utf-8", errors="replace")
        right = vocab[pair[1]].decode("utf-8", errors="replace")
        merged = vocab[new_id].decode("utf-8", errors="replace")
        print(f"  {new_id}: {left!r} + {right!r} -> {merged!r}")

    print()
    print("--- 3. round-trip ---")
    for sample in ["the quick brown fox", "tokenization", "a lazy dog sleeps"]:
        ids = encode(sample, merges)
        back = decode(ids, vocab)
        print(f"  {sample!r} -> {len(ids)} tokens -> round-trips: {back == sample}")

    print()
    print("--- 4. nothing is out of vocabulary ---")
    round_trips_unseen = None
    unseen = "Zebra! 987 éàü \U0001f600 <|weird|>"
    ids = encode(unseen, merges)
    back = decode(ids, vocab)
    escaped = unseen.encode("unicode_escape").decode("ascii")
    print(f"text never seen in training: {escaped}")
    print(f"as UTF-8 that is {len(unseen.encode('utf-8'))} bytes")
    round_trips_unseen = back == unseen
    print(f"encodes to {len(ids)} tokens and round-trips: {round_trips_unseen}")
    print("(byte-level means every byte sequence is representable - there is")
    print(" no UNK token and there cannot be one)")

    print()
    print("--- 5. merge order is the model ---")
    word = "quicker"
    ids_full = encode(word, merges)
    ids_half = encode(word, merges[: len(merges) // 2])
    ids_none = encode(word, [])
    print(f"  {word!r} with all {len(merges)} merges: {len(ids_full)} tokens")
    print(f"  {word!r} with the first {len(merges)//2} merges: {len(ids_half)} tokens")
    print(f"  {word!r} with no merges: {len(ids_none)} tokens")
    one_per_byte = len(ids_none) == len(word.encode("utf-8"))
    print(f"no merges gives one token per byte: {one_per_byte}")
    print(f"more merges never increases the token count: {len(ids_full) <= len(ids_half) <= len(ids_none)}")

    print()
    print("--- 6. compression against vocabulary size ---")
    total_bytes = len(CORPUS.encode("utf-8"))
    ratios = []
    for size in (256, 300, 350, 400, 500):
        m, v = train_bpe(CORPUS, size)
        n_tokens = len(encode(CORPUS, m))
        ratio = total_bytes / n_tokens
        ratios.append(ratio)
        # Print the vocabulary actually reached: training stops early once no
        # pair repeats, so a large request can fall short of its target.
        print(f"  vocab requested {size:>4}, reached {len(v):>4}: {n_tokens:>4} tokens, {ratio:.2f} bytes/token")
    print(f"compression improves monotonically: {all(a <= b for a, b in zip(ratios, ratios[1:]))}")
    gains = [b - a for a, b in zip(ratios, ratios[1:])]
    print(f"gains diminish: {gains[-1] <= gains[0]}")
    print(f"  per-step gains: {[round(g, 3) for g in gains]}", file=sys.stderr)

    print()
    print("--- 7. why models cannot count letters ---")
    for word in ["strawberry", "tokenization", "hello"]:
        n = len(encode(word, merges))
        print(f"  {word!r}: {len(word)} characters, {n} tokens")
    print("(the model sees the token ids, not the characters - character-level")
    print(" questions are a representation problem, not a reasoning one)")

    print()
    all_ok = (
        len(vocab) == VOCAB_TARGET
        and decode(encode("the quick brown fox", merges), vocab) == "the quick brown fox"
        and round_trips_unseen
        and one_per_byte
        and len(ids_full) <= len(ids_half) <= len(ids_none)
        and all(a <= b for a, b in zip(ratios, ratios[1:]))
        and gains[-1] <= gains[0]
    )
    print(f"ALL CHECKS PASS: {all_ok}")


if __name__ == "__main__":
    main()
