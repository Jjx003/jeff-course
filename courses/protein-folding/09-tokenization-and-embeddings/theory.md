## Why "tokenize" anything?

Transformers operate on sequences of integers, not strings. Tokenization
is the unglamorous bridge between human-readable text and the integer
tensor a neural network actually consumes. For natural language this
is the hard part — should "playing" be one token or `play` + `ing`?
Should rare words break into characters? — and entire libraries
(`sentencepiece`, `tokenizers`, `tiktoken`) are devoted to it.

Proteins are mercifully simple. The alphabet is fixed at 20 letters
plus a handful of special and ambiguity codes, every letter is a unit
of biological meaning, and there's no useful sub-letter decomposition.
So protein tokenizers are essentially:

1. Map each amino-acid letter to a unique integer.
2. Add a few special tokens for transformer machinery.
3. Optionally handle padding and attention masks for batching.

That's it. ESM-2's tokenizer is ~50 lines of Python.

## ESM-2's exact vocabulary

The HuggingFace `facebook/esm2_t6_8M_UR50D` tokenizer (which is shared
across every ESM-2 size — 8M, 35M, 150M, 650M, 3B, 15B) has 33
entries:

| Token | ID | Notes |
|---|---|---|
| `<cls>` | 0 | Prepended to every input — "classification" / summary slot |
| `<pad>` | 1 | Filler for variable-length batches |
| `<eos>` | 2 | Appended to every input — "end of sequence" |
| `<unk>` | 3 | Anything outside the alphabet |
| L, A, G, V, S, E, R, T, I, D, P, K, Q, N, F, Y, M, H, W, C | 4–23 | The 20 standard amino acids, in frequency order |
| X, B, U, Z, O | 24–28 | IUPAC ambiguity / non-canonical codes |
| `.`, `-` | 29, 30 | Padding and gap characters |
| `<null_1>` | 31 | Reserved |
| `<mask>` | 32 | Used during masked-language-model training |

Two practical consequences:

1. The alphabet is **not in alphabetical order** — it's roughly in
   descending order of natural amino-acid frequency (L, A, G are the
   three most common AAs in UniProt). When debugging, never assume
   `A=4` and `B=5`; always go through `tokenizer.convert_tokens_to_ids`.
2. Calling `tokenizer(seq)` adds `<cls>` and `<eos>` automatically.
   If you need just the per-residue IDs (e.g. to feed an external
   model), pass `add_special_tokens=False`.

## Embeddings as a learned dictionary

After tokenization, the next step in any transformer is the **embedding
lookup**:

$$\mathbf{e}_t = E[t, :], \qquad E \in \mathbb{R}^{V \times d}$$

where $V$ is vocabulary size, $d$ is the embedding dimension (320 for
ESM-2 8M, up to 5120 for ESM-2 15B), and $t$ is a token ID.

Implementation-wise this is a single array index. Conceptually it's
**a learned dictionary**: each token has a $d$-dimensional vector that
gets gradually shaped by training. Similar tokens — chemically similar
amino acids in our case — drift to similar embeddings.

Because the embedding lookup is differentiable (it's just `gather`),
gradients flow back into the embedding matrix during training. The
embedding for `L` ends up close to the embedding for `I` not because
we hand-coded that fact but because the loss landscape pushes them
together.

In code, the matrix lives at:

```python
model.embeddings.word_embeddings.weight    # shape (33, 320)
```

and a "lookup" is just

```python
m_id = tokenizer.convert_tokens_to_ids("M")    # 20
m_vec = model.embeddings.word_embeddings.weight[m_id]   # shape (320,)
```

That's the entire embedding subsystem of ESM-2 — three lines.

## Positional encodings

A bare embedding vector tells the model *what* token is at each
position but not *where* it is in the sequence. Without positional
information, attention is permutation-invariant — the model would
treat `MGLSDGEW` and `WGLSDGEM` as identical.

Two common solutions:

### Sinusoidal (Vaswani et al, 2017)

Fixed, non-learned, formula-defined. For position $p$ and dimension $j$
of an embedding of size $d$:

$$\text{PE}(p, 2k) = \sin\!\left( \frac{p}{10000^{2k/d}} \right)$$

$$\text{PE}(p, 2k+1) = \cos\!\left( \frac{p}{10000^{2k/d}} \right)$$

You add the positional encoding to the embedding before feeding the
transformer the residual stream:

$$\mathbf{x}_p = \mathbf{e}_{t_p} + \text{PE}(p)$$

The intuition is geometric: each pair of $(\sin, \cos)$ dimensions
corresponds to a "clock" of a different frequency, so the model can
read both fine-grained and coarse-grained positional information out
of the encoding.

### Rotary (RoPE, Su et al, 2021)

What ESM-2 actually uses. Instead of *adding* positional information
to the embedding, RoPE **rotates** pairs of dimensions in the query
and key vectors at attention time, by an angle proportional to
position. The dot product $\mathbf{q}_i \cdot \mathbf{k}_j$ then
naturally depends on the relative position $i - j$.

RoPE is more expressive than additive sinusoidal encodings, generalises
better to sequences longer than seen in training, and has effectively
become the standard for modern transformers (LLaMA, ESM-2, Gemma, etc.).

We won't dig into positional encodings in this module — the next
module is the right place — but you'll see them implicitly in
modules 11+.

## The two production tokenizer APIs

### HuggingFace (`transformers`) — what we use

```python
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("facebook/esm2_t6_8M_UR50D")
ids = tok("MGLSDGEW")["input_ids"]
# [0, 20, 6, 4, 8, 13, 6, 9, 22, 2]
```

This is the canonical interface for the rest of the course. It
integrates with `EsmModel`, `EsmForMaskedLM`, batching, attention
masks, and PyTorch tensors.

### `fair-esm` (Meta's original release)

```python
import esm
model, alphabet = esm.pretrained.esm2_t6_8M_UR50D()
batch_converter = alphabet.get_batch_converter()
_, _, tokens = batch_converter([("seq1", "MGLSDGEW")])
```

Same vocabulary, slightly different API. It also uses different
integer IDs for some tokens (e.g. `<cls>` is 0 in both, but the
amino-acid order can differ from older ESM-1 alphabets). For this
course we standardise on the HuggingFace integer assignments.

## Embedding dimensions in practice

Some real numbers from the ESM-2 family:

| Model | Layers | Embed dim | Heads |
|---|---|---|---|
| ESM-2 8M | 6 | 320 | 20 |
| ESM-2 35M | 12 | 480 | 20 |
| ESM-2 150M | 30 | 640 | 20 |
| ESM-2 650M | 33 | 1280 | 20 |
| ESM-2 3B | 36 | 2560 | 40 |
| ESM-2 15B | 48 | 5120 | 40 |

Our exercise uses ESM-2 8M with $d = 320$. The pattern of "wider is
bigger model is better up to a point" is what module 13 explores.
