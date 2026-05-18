## Goal

Use the **HuggingFace ESM-2 tokenizer** (the smallest checkpoint,
`facebook/esm2_t6_8M_UR50D`, ~30 MB) to:

1. Encode a protein sequence into a list of integer token IDs,
   including the `<cls>` and `<eos>` special tokens.
2. Print the model's special-token IDs (`<cls>`, `<pad>`, `<eos>`,
   `<unk>`, `<mask>`) so you can see how the vocabulary is laid out.
3. Look up the **learned embedding** for one residue by indexing into
   the model's `word_embeddings.weight` matrix and confirming that
   "embedding lookup" really is just an array index.

This is the first piece of a real protein language model — the same
two operations (tokenize, embed) prefix every ESM-2 forward pass you
will see for the rest of the course.

## Why a real tokenizer (and not a toy one)?

A toy "20 letters → 20 IDs" map is enough to write down the *idea* of
tokenization, but every single later module loads ESM-2 from
HuggingFace and you'll need to know its exact conventions: that
`<cls>` is prepended at id `0`, `<eos>` is appended at id `2`, and
that the vocabulary has `33` entries (20 standard amino acids + 8
ambiguity / null codes + 5 special tokens). Getting this right once,
here, saves you debugging confusing off-by-one errors in modules 11,
12, 13, 18, 20, and 21.

## ESM-2 vocabulary

`facebook/esm2_t6_8M_UR50D` (and every other ESM-2 size — they share a
tokenizer) ships with **33 tokens**:

| Type | Tokens |
|---|---|
| Special | `<cls>`, `<pad>`, `<eos>`, `<unk>`, `<mask>` |
| Standard amino acids (20) | `A C D E F G H I K L M N P Q R S T V W Y` |
| IUPAC ambiguity codes | `B` (D/N), `Z` (E/Q), `X` (any), `U` (selenocysteine), `O` (pyrrolysine), `J` |
| Filler / structural | `.`, `-`, `<null_1>` |

You don't need to memorise the exact integer assignments — the
tokenizer object exposes them via `tokenizer.cls_token_id`,
`tokenizer.mask_token_id`, etc. The two relevant facts for this
exercise are:

- `tokenizer.vocab_size == 33`.
- Calling `tokenizer(seq)` automatically prepends `<cls>` and appends
  `<eos>`, so a sequence of length $L$ becomes a token list of
  length $L + 2$.

## The sequence

```text
MGLSDGEW
```

The first 8 residues of human myoglobin. After tokenization with
defaults this becomes a list of length 10.

## Required output (exact)

```text
ESM-2 tokenizer: facebook/esm2_t6_8M_UR50D
  vocab_size: 33
  <cls>=0  <pad>=1  <eos>=2  <unk>=3  <mask>=32

Sequence: MGLSDGEW (length 8)
  Token IDs: [0, 20, 6, 4, 8, 13, 6, 9, 22, 2]
  Encoded length (with <cls>/<eos>): 10
  Distinct token IDs: 9
  Per-residue IDs:
    pos  1  M -> 20
    pos  2  G -> 6
    pos  3  L -> 4
    pos  4  S -> 8
    pos  5  D -> 13
    pos  6  G -> 6
    pos  7  E -> 9
    pos  8  W -> 22

Loaded ESM-2 8M model
  embedding matrix shape: (33, 320)

Embedding for 'M' (token id 20)
  shape: (320,)
  first 4 values: [-0.1202, -0.0626, -0.0312, 0.0082]
  last 4 values: [-0.4539, -0.2532, 0.0479, -0.0889]
  sum of all 320 values: -4.5855
```

The first time you run this, the script downloads ~30 MB of weights;
afterwards everything is cached and the script runs in a second or
two. The numbers above are **byte-for-byte deterministic** — they come
straight from the published checkpoint and don't depend on a random
seed.

## What you should learn

- **Tokenization is a dictionary lookup.** `tokenizer("MGLSDGEW")`
  walks the string, looks each character up in a vocab dict, and
  wraps the result with `<cls>` and `<eos>`. There is no magic.
- **Embedding lookup is an array index.** When a transformer "embeds"
  a token, it does `embedding_matrix[token_id]` — exactly the same
  operation you'd write with a numpy array. The interesting bit is
  that the rows of `embedding_matrix` are **learned** during
  pretraining; chemically similar amino acids end up with similar
  embedding vectors.
- **Special tokens are scaffolding.** `<cls>` is a "summary"
  position; its embedding after the transformer is often used as a
  single-vector representation of the whole sequence. `<mask>` is the
  placeholder used during masked-language-model training (next
  module). `<pad>` exists so we can stuff variable-length sequences
  into a uniform tensor for batching.
- **Vocabulary size is a design choice.** ESM-2's vocab is 33 tokens.
  Compare to GPT-style English tokenizers: ~50,000 BPE merges.
  Proteins use a tiny vocab because the underlying alphabet is small
  and meaningful — every letter is a whole amino acid, not a
  sub-word piece.
