## Walkthrough

### Loading the tokenizer

```python
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("facebook/esm2_t6_8M_UR50D")
```

`AutoTokenizer` looks at the checkpoint's `tokenizer_config.json` and
returns the right class — for ESM-2 that's `EsmTokenizer`, a thin
subclass of `PreTrainedTokenizer` that walks the input string
character-by-character and looks each one up in a 33-entry vocab.

The five special-token IDs are exposed as attributes on the
tokenizer (`tokenizer.cls_token_id`, etc). We print them out so the
user can see the layout — and so the rest of the course can index
into the logits without any magic numbers.

### Encoding the sequence

```python
ids = tokenizer("MGLSDGEW")["input_ids"]
# [0, 20, 6, 4, 8, 13, 6, 9, 22, 2]
```

Calling the tokenizer like a function is shorthand for
`tokenizer.encode_plus(...)`. The default behaviour adds special
tokens (`<cls>` at the front, `<eos>` at the back) and returns a
plain Python `list` for the IDs (or a tensor if you ask for
`return_tensors="pt"`).

The resulting list has length 10:
- index 0: `<cls>` (id 0)
- indices 1–8: the eight residues `M, G, L, S, D, G, E, W`
- index 9: `<eos>` (id 2)

### Per-residue ID readout

```python
aa_ids = ids[1:-1]                      # strip <cls> and <eos>
for i, (aa, tid) in enumerate(zip(SEQUENCE, aa_ids), start=1):
    print(f"    pos {i:>2}  {aa} -> {tid}")
```

This is the part where you get to confirm — by eye — that ESM-2's
alphabet really is what `theory.md` says. `M` is `20`, `G` is `6`,
`L` is `4`. The list is *not* alphabetical because the ESM-2 authors
ordered amino acids by their natural frequency in UniProt
(`L A G V S E R T I D P K Q N F Y M H W C`).

### Loading the model and reading its embedding matrix

```python
from transformers import EsmModel
model = EsmModel.from_pretrained("facebook/esm2_t6_8M_UR50D")
model.eval()

embedding_matrix = model.embeddings.word_embeddings.weight
```

This downloads the 8M-parameter ESM-2 weights (~30 MB) the first time
it runs and caches them under `~/.cache/huggingface/hub/`. Subsequent
calls are instant.

`model.embeddings.word_embeddings` is a `torch.nn.Embedding` layer.
Its `.weight` is a `(vocab_size, hidden_size) = (33, 320)` matrix
that serves as the lookup table. Every transformer in existence has
some form of this matrix as its first layer.

### The lookup

```python
m_id = tokenizer.convert_tokens_to_ids("M")    # 20
m_vec = embedding_matrix[m_id]                 # shape (320,)
```

This is **the** operation. Indexing a row out of a learned matrix is
all that "embedding" means at the implementation level. Every
forward pass of every PLM in the course starts with this exact step
(repeated once per residue).

The values are deterministic — we're reading bits out of a published
checkpoint, no random seeds involved. For 'M' the first four entries
are `[-0.1202, -0.0626, -0.0312, 0.0082]` and the last four are
`[-0.4539, -0.2532, 0.0479, -0.0889]`, summing to `-4.5855` across
all 320 dimensions. If your numbers differ, the most likely causes
are:

- A different checkpoint was loaded (double-check the string
  `facebook/esm2_t6_8M_UR50D`).
- You converted to FP16 somewhere; we keep the default FP32 here.
- A network glitch corrupted the cached weights — clear
  `~/.cache/huggingface/hub/models--facebook--esm2_t6_8M_UR50D/` and
  re-run.

## Why bother loading the model if we're not running it?

Two reasons:

1. **It makes the abstraction concrete.** "Embedding lookup is just
   indexing a matrix" is much more convincing when the matrix is a
   real, published, 33×320 grid of floats than when it's a toy
   array generated from a formula.
2. **Every later module reuses this exact loading code.** Module 11
   masks a residue and runs a forward pass. Module 12 extracts
   per-position embeddings. Module 18 reuses the same checkpoint for
   structure prediction. Getting the import + load + eval pattern
   into your fingers now pays off four modules later.

## Connection to the rest of the course

What we just built is the *first half-millisecond* of an ESM-2
forward pass. The remaining steps:

1. Add positional information (RoPE — see theory.md).
2. Stack 6 self-attention + feedforward blocks (the next module is
   the conceptual deep-dive on what self-attention is doing).
3. Output a per-position vector that's much richer than the bare
   embedding (module 12 demonstrates this with cosine similarity).
4. Plug a "structure module" or "contact head" or "MLM prediction
   head" on top of those vectors, depending on the task (modules 11,
   18, 20).

If you can tokenize, look up an embedding, and inspect the matrix
shape with the code in this module, you can already read every
production PLM script you'll encounter in this track.
