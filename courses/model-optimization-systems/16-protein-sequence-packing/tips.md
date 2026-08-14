# Hints

Get Part 1 printing the right pack occupancy before you load ESM-2. The
checkpoint is small, but a packing bug is cheaper to find on integers than on
hidden states.

## First-fit decreasing

Sort by token length, not residue length. Then scan existing packs in the
order they were opened:

```python
for item in sorted(items, key=lambda pair: -pair[1]):
    length = item[1]
    for index, room in enumerate(used):
        if room + length <= capacity:
            packs[index].append(item)
            used[index] = room + length
            break
    else:
        packs.append([item])
        used.append(length)
```

The `else` on a `for` fires when no existing pack had room. Opening a new pack
"just in case" at the start of the loop produces one sequence per pack and
erases the win.

## The block-diagonal mask

`keep` has shape `(n_packs, 1, capacity, capacity)`. For a segment at
`(pack_index, start, length)`:

```python
keep[pack_index, 0, start:start+length, start:start+length] = 1.0
```

The singleton head dimension is what lets the additive mask broadcast over
ESM-2's 20 heads. `to_additive` is then:

```python
return (1.0 - keep) * torch.finfo(torch.float32).min
```

Using `float("-inf")` directly is fine in isolation and will NaN a softmax if
an entire row is masked (the pad rows). The starter's padding mask already
drops those rows from the embedding output's effective content, but the
`finfo.min` form is the one that stays finite under every reduction.

## Why `encode_packed` bypasses `EsmModel.forward`

If you call `model(input_ids=..., attention_mask=four_d)` HuggingFace raises.
If you pass a 3D mask, `EsmEmbeddings` treats it as a per-token pad indicator
and indexes it wrong. The given helper sends the 2D pad mask to embeddings and
the 4D additive mask to the encoder. Do not "simplify" this back into a single
`model(...)` call; it will not work on this class.

## Common mistakes

- Packing by residue length and then being surprised that a 126-residue pair
  plus two special tokens overflows capacity 128.
- A 2D mask used as if it were block-diagonal. The negative control is
  exactly this bug; if your "packed" path matches the negative control, you
  shipped the bug.
- Comparing full packed rows against standalone sequences, pad tokens
  included. Slice each segment to `start:start+length`.
- Using `torch.equal` on embeddings. The encoder's fused kernels are allowed
  a few ulps; `allclose(..., atol=1e-5)` is the check the grader wants.
- Resetting position IDs on ESM-2 and concluding that packing always needs
  that, or *not* resetting them on a BERT-style trunk and concluding that
  packing never needs it. The toy block exists so you can see both.
- Reporting only the padding-waste win and skipping Part 3. The packed dense
  kernel does *more* attention work than naive padding on this set.

## Sanity checks

- Token counts are residue counts plus 2. Ubiquitin is 76 residues and 78
  tokens. Total useful tokens: `472`.
- Naive arrival-order padding: `792` slots, `40.4%` waste.
- Length-bucketed padding: `610` slots, `22.6%` waste.
- FFD, capacity 128: 4 packs, `512` slots, `7.8%` waste. Pack occupancies
  `98.4%`, `99.2%`, `99.2%`, `71.9%`.
- Padded batching matches standalone `14 of 14`.
- Packed block-diagonal matches standalone `14 of 14`.
- Padding-only packed batch matches `0 of 14`. Worst relative corruption
  prints as `64%`, least as `23%`.
- Toy block: per-segment positions `14 of 14`, continuous positions `4 of 14`
  (the four segments that sit at offset 0).
- Part 3: packed dense score entries `65536`, block-sparse ideal `20966`,
  ratio `3.13x`. Packed dense vs naive padded: `1.35x` *more*, not less.

## Going deeper

- Drop `<eos>` from every sequence (or don't add it) and re-pack. The fourth
  pack's occupancy jumps because five short peptides currently leave 36 slots
  free, some of which were special tokens.
- Swap ESM-2 for a tiny BERT-style encoder with learned positions and watch
  Part 2b pass only after you wire `segment_position_ids` into the real
  forward, not just the toy block.
- Implement worst-fit decreasing instead of first-fit and compare pack count.
  On this set they tie; on a more skewed length distribution they do not.

## References

- Lin et al., *Evolutionary-scale prediction of atomic-level protein structure
  with a language model*, Science 2023. ESM-2 / ESMFold; rotary embeddings
  and the 8M–15B scale ladder.
- Raffel et al., *Exploring the Limits of Transfer Learning with a Unified
  Text-to-Text Transformer*, JMLR 2020. T5; example packing as a pretraining
  default, with the same block-diagonal-mask contract.
- Krell et al., *Efficient Sequence Packing without Cross-contamination:
  Accelerating Large Language Models without Impacting Performance*, 2021.
  The packing-plus-isolation argument stated for language models generally.
- Johnson, *Near-optimal bin packing algorithms*, PhD thesis, MIT 1973. The
  $\frac{11}{9}\mathrm{OPT}+1$ bound on first-fit decreasing.
