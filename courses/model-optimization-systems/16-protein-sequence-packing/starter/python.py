"""
Sequence packing for protein language models, verified against real ESM-2.

Part 1 packs real tokenized protein sequences with first-fit decreasing.
Part 2 proves that a packed batch produces the same per-residue embeddings as
running each sequence alone, using the real facebook/esm2_t6_8M_UR50D
checkpoint, and then shows the packed batch breaking when the mask is wrong.
Part 3 accounts for what packing actually costs.

Everything graded runs on CPU in float32 with seed 0. Absolute embedding values
never reach stdout, because they would pin the grader to one checkpoint revision
and one library version. stdout carries integers, shapes, booleans from
torch.allclose, and packing percentages. Wall-clock timing and raw difference
magnitudes go to stderr, which is shown to you but not graded.

The first run downloads about 30 MB from Hugging Face.
"""

from transformers.utils import logging as hf_logging

hf_logging.set_verbosity_error()

import math
import sys
import time

import torch
from transformers import AutoTokenizer, EsmModel

CHECKPOINT = "facebook/esm2_t6_8M_UR50D"
PACK_CAPACITY = 128
NAIVE_BATCH_SIZE = 4
ATOL = 1e-5
TOY_DIM = 64
TOY_HEADS = 4
BIG_CAPACITY = 8192
BIG_PACKS = 8

# Real amino-acid sequences, listed in arrival order rather than sorted, which
# is what a serving queue actually hands you.
SEQUENCES = [
    ("ubiquitin", "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"),
    ("oxytocin", "CYIQNCPLG"),
    ("crambin", "TTCCPSIVARSNFNVCRLPGTPEAICATYTGCIIIPGATCPGDYAN"),
    ("bradykinin", "RPPGFSPFR"),
    ("aprotinin", "RPDFCLEPPYTGPCKARIIRYFYNAKAGLCQTFVYGGCRAKRNNFKSAEDCMRTCGGA"),
    ("vasopressin", "CYFQNCPRG"),
    ("acth", "SYSMEHFRWGKPVGKKRRPVKVYPNGAEDESAEAFPLEF"),
    ("somatostatin", "AGCKNFFWKTFTSC"),
    ("amyloid_beta", "DAEFRHDSGYEVHHQKLVFFAEDVGSNKGAIIGLMVGGVVIA"),
    ("insulin_a", "GIVEQCCTSICSLYQLENYCN"),
    ("neuropeptide_y", "YPSKPDNPGEDAPAEDMARYYSALRHYINLITRQRY"),
    ("melittin", "GIGAVLKVLTTGLPALISWIKRKRQQ"),
    ("glucagon", "HSQGTFTSDYSKYLDSRRAQDFVQWLMNT"),
    ("insulin_b", "FVNQHLCGSHLVEALYLVCGERGFFYTPKT"),
]


def padded_slots(lengths, batch_size: int) -> int:
    """Total token slots when `lengths` is batched in order and each batch is
    padded to its own longest sequence."""
    # TODO 1: Walk `lengths` in slices of `batch_size`. Each slice costs
    # len(slice) * max(slice) slots. Sum those. Do not sort: the caller decides
    # whether the input arrives in arrival order or sorted order.
    raise NotImplementedError


def padded_rows(lengths, batch_size: int):
    """The per-row sequence length each sequence is actually padded out to.

    Same batching as padded_slots, but returned as one length per row so Part 3
    can square them. A batch of lengths [44, 23, 38, 28] becomes
    [44, 44, 44, 44].
    """
    # TODO 2: Return a flat list with len(slice) copies of max(slice) for each
    # slice of `batch_size`.
    raise NotImplementedError


def first_fit_decreasing(items, capacity: int):
    """Pack (name, token_length) pairs into bins of at most `capacity` tokens.

    Returns a list of packs, each a list of (name, token_length) in placement
    order.
    """
    # TODO 3: Sort items by descending token length, then for each item scan the
    # existing packs in order and append it to the first one with room. Open a
    # new pack only when none fits. Track each pack's used total as you go
    # rather than re-summing it, and sort with key=lambda pair: -pair[1] so ties
    # keep arrival order and the packing stays deterministic.
    raise NotImplementedError


def build_packed_batch(packs, encoded: dict, capacity: int, pad_id: int):
    """Materialize the packs as tensors.

    Returns (input_ids, padding_mask, segments) where

      input_ids    long, (n_packs, capacity), pad_id in unused slots
      padding_mask float32, (n_packs, capacity), 1.0 on real tokens
      segments     list of (pack_index, name, start, length), one per sequence

    `segments` is the boundary bookkeeping that everything downstream needs. A
    packed batch without it is unusable.
    """
    # TODO 4: Start input_ids full of pad_id and padding_mask full of zeros.
    # For each pack, walk its items keeping a running offset, copy
    # encoded[name] into input_ids[pack_index, offset:offset + length], set the
    # matching padding_mask entries to 1.0, record the segment, and advance the
    # offset by `length`.
    raise NotImplementedError


def block_diagonal_keep_mask(segments, n_packs: int, capacity: int) -> torch.Tensor:
    """Float32 (n_packs, 1, capacity, capacity) mask, 1.0 where attention is allowed.

    A 2D (batch, seq) mask can only say "this slot is padding". It cannot say
    "these two real tokens belong to different proteins", which is exactly the
    statement packing needs.
    """
    # TODO 5: Start from zeros and set the square block
    # [start:start + length, start:start + length] to 1.0 for every segment.
    # Everything outside those blocks, including all padding, stays 0.0.
    raise NotImplementedError


def padding_keep_mask(padding_mask: torch.Tensor) -> torch.Tensor:
    """The negative control: broadcast a padding-only mask to 4D.

    Every real token may attend to every other real token in its pack,
    including tokens from other proteins.
    """
    return padding_mask[:, None, None, :].expand(-1, 1, padding_mask.shape[1], -1).contiguous()


def to_additive(keep: torch.Tensor) -> torch.Tensor:
    """Turn a 0/1 keep-mask into the additive pre-softmax bias the encoder wants."""
    # TODO 6: Return (1.0 - keep) * torch.finfo(torch.float32).min, so allowed
    # pairs get +0.0 and forbidden pairs get a bias that softmaxes to exactly
    # zero weight. Use finfo.min rather than -inf: a fully masked padding row
    # would otherwise produce NaN instead of harmless garbage.
    raise NotImplementedError


def segment_position_ids(segments, n_packs: int, capacity: int) -> torch.Tensor:
    """Long (n_packs, capacity) position ids that restart at every segment."""
    # TODO 7: Start from zeros and write torch.arange(length) into
    # position_ids[pack_index, start:start + length] for each segment. Position
    # ids must not run continuously across a pack: the third protein in a pack
    # is still at its own position 0, not at position 104.
    raise NotImplementedError


def encode_packed(model, input_ids: torch.Tensor, padding_mask: torch.Tensor, additive: torch.Tensor):
    """Run ESM-2 with an arbitrary 4D additive attention mask.

    EsmModel.forward cannot express this. It rejects a 4D mask outright, and a
    3D mask crashes inside the embedding layer, which reuses the same tensor as
    a per-token padding mask. So the 2D padding mask goes to the embeddings and
    the block-diagonal mask goes straight to the encoder, which already expects
    an additive (batch, 1, seq, seq) bias.
    """
    embedding_output = model.embeddings(input_ids=input_ids, attention_mask=padding_mask)
    return model.encoder(embedding_output, attention_mask=additive).last_hidden_state


def make_toy_params(vocab_size: int, dim: int, capacity: int):
    generator = torch.Generator().manual_seed(0)
    scale = dim**-0.5
    names = ("token", "position", "wq", "wk", "wv", "wo")
    shapes = (
        (vocab_size, dim),
        (capacity, dim),
        (dim, dim),
        (dim, dim),
        (dim, dim),
        (dim, dim),
    )
    return {
        name: torch.randn(*shape, generator=generator) * scale
        for name, shape in zip(names, shapes)
    }


def toy_block(params, token_ids: torch.Tensor, position_ids: torch.Tensor, additive: torch.Tensor):
    """One self-attention block with learned absolute position embeddings.

    ESM-2 uses rotary position embeddings, which depend only on i - j and are
    therefore immune to segment offsets. This block is the opposite case, and
    it is the common one: BERT, RoBERTa, ESM-1b, and any model with a learned
    position table breaks if position ids run continuously across a pack.
    """
    x = params["token"][token_ids] + params["position"][position_ids]
    batch, seq, dim = x.shape
    head_dim = dim // TOY_HEADS

    def heads(t):
        return t.view(batch, seq, TOY_HEADS, head_dim).transpose(1, 2)

    q = heads(x @ params["wq"])
    k = heads(x @ params["wk"])
    v = heads(x @ params["wv"])

    scores = q @ k.transpose(-1, -2) / math.sqrt(head_dim) + additive
    weights = scores.softmax(dim=-1)
    context = (weights @ v).transpose(1, 2).reshape(batch, seq, dim)
    return context @ params["wo"]


def score_entries(rows) -> int:
    """Attention query-key pairs a dense kernel evaluates for these row lengths."""
    # TODO 8: Attention is quadratic in the row length, so a row of length S
    # costs S * S score entries. Sum that over rows and return an int.
    raise NotImplementedError


def relative_error(reference: torch.Tensor, other: torch.Tensor) -> float:
    return float((reference - other).norm() / reference.norm())


def main() -> None:
    torch.manual_seed(0)

    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
    model = EsmModel.from_pretrained(CHECKPOINT, add_pooling_layer=False)
    model.eval()
    config = model.config

    print("=== Sequence packing, verified against real ESM-2 ===")
    print(f"checkpoint: {CHECKPOINT}")
    print(f"hidden size: {config.hidden_size}")
    print(f"layers: {config.num_hidden_layers}")
    print(f"attention heads: {config.num_attention_heads}")
    print(f"position embedding type: {config.position_embedding_type}")
    print(f"pack capacity: {PACK_CAPACITY}")
    print()

    encoded = {name: tokenizer(seq)["input_ids"] for name, seq in SEQUENCES}
    items = [(name, len(encoded[name])) for name, _ in SEQUENCES]
    lengths = [length for _, length in items]
    residues = sum(len(seq) for _, seq in SEQUENCES)

    print("--- part 1: real tokenized lengths ---")
    for (name, seq), (_, length) in zip(SEQUENCES, items):
        print(f"  {name:<15} residues={len(seq):>3} tokens={length:>3}")
    print(f"  sequences: {len(items)}")
    print(f"  residues: {residues}")
    print(f"  tokens with <cls>/<eos>: {sum(lengths)}")
    print(f"  special-token overhead: {sum(lengths) - residues}")
    print()

    naive_slots = padded_slots(lengths, NAIVE_BATCH_SIZE)
    bucketed_lengths = sorted(lengths, reverse=True)
    bucketed_slots = padded_slots(bucketed_lengths, NAIVE_BATCH_SIZE)
    packs = first_fit_decreasing(items, PACK_CAPACITY)
    packed_slots = len(packs) * PACK_CAPACITY
    useful = sum(lengths)

    print("--- part 1: padding waste ---")
    print(f"  useful tokens: {useful}")
    print(f"  naive batching, batch {NAIVE_BATCH_SIZE}, arrival order")
    print(f"    padded slots: {naive_slots}")
    print(f"    wasted slots: {naive_slots - useful} ({(naive_slots - useful) / naive_slots * 100:.1f}%)")
    print(f"  length-bucketed batching, batch {NAIVE_BATCH_SIZE}, sorted")
    print(f"    padded slots: {bucketed_slots}")
    print(f"    wasted slots: {bucketed_slots - useful} ({(bucketed_slots - useful) / bucketed_slots * 100:.1f}%)")
    print(f"  first-fit-decreasing packing, capacity {PACK_CAPACITY}")
    print(f"    packs: {len(packs)}")
    print(f"    allocated slots: {packed_slots}")
    print(f"    wasted slots: {packed_slots - useful} ({(packed_slots - useful) / packed_slots * 100:.1f}%)")
    for index, pack in enumerate(packs, start=1):
        pack_used = sum(length for _, length in pack)
        names = ",".join(name for name, _ in pack)
        print(
            f"    pack {index}: segments={len(pack)} used={pack_used} "
            f"free={PACK_CAPACITY - pack_used} "
            f"occupancy={pack_used / PACK_CAPACITY * 100:.1f}% items={names}"
        )
    print(f"  slots saved vs naive: {naive_slots - packed_slots} ({(naive_slots - packed_slots) / naive_slots * 100:.1f}% fewer)")
    print(f"  slots saved vs bucketed: {bucketed_slots - packed_slots} ({(bucketed_slots - packed_slots) / bucketed_slots * 100:.1f}% fewer)")
    print()

    # Reference: every sequence on its own, one forward pass each.
    standalone = {}
    started = time.perf_counter()
    with torch.inference_mode():
        for name, length in items:
            ids = torch.tensor([encoded[name]])
            out = model(input_ids=ids, attention_mask=torch.ones(1, length)).last_hidden_state
            standalone[name] = out[0].clone()
    single_seconds = time.perf_counter() - started
    print(f"[measured] {len(items)} standalone forwards: {single_seconds * 1000:.1f} ms", file=sys.stderr)

    max_length = max(lengths)
    batch_ids = torch.full((len(items), max_length), tokenizer.pad_token_id, dtype=torch.long)
    batch_mask = torch.zeros(len(items), max_length)
    for row, (name, length) in enumerate(items):
        batch_ids[row, :length] = torch.tensor(encoded[name])
        batch_mask[row, :length] = 1.0

    with torch.inference_mode():
        batched = model(input_ids=batch_ids, attention_mask=batch_mask).last_hidden_state

    # TODO 9: Compare the padded batch against the standalone references.
    # For row `row` holding a sequence of `length` real tokens, the useful part
    # of the batched output is batched[row, :length]. Build a list of
    # torch.allclose(standalone[name], batched[row, :length], atol=ATOL) and
    # replace the placeholder below. This is the plain-padding property, and
    # getting it wrong is a real production bug: an inverted or missing padding
    # mask silently changes every embedding in the batch.
    padded_matches = [False] * len(items)

    print("--- part 2a: padded batching equals one-at-a-time ---")
    print(f"  batch input_ids shape: {tuple(batch_ids.shape)}")
    print(f"  padding mask shape: {tuple(batch_mask.shape)}")
    print(f"  sequences matching standalone: {sum(padded_matches)} of {len(items)}")
    print(f"  all match: {all(padded_matches)}")
    print()

    input_ids, padding_mask, segments = build_packed_batch(
        packs, encoded, PACK_CAPACITY, tokenizer.pad_token_id
    )
    block_keep = block_diagonal_keep_mask(segments, len(packs), PACK_CAPACITY)
    block_additive = to_additive(block_keep)
    pad_keep = padding_keep_mask(padding_mask)
    pad_additive = to_additive(pad_keep)

    started = time.perf_counter()
    with torch.inference_mode():
        packed_out = encode_packed(model, input_ids, padding_mask, block_additive)
        leaky_out = encode_packed(model, input_ids, padding_mask, pad_additive)
    packed_seconds = time.perf_counter() - started
    print(f"[measured] {len(packs)} packed forwards (x2): {packed_seconds * 1000:.1f} ms", file=sys.stderr)

    print("--- part 2b: block-diagonal packing equals standalone ---")
    print(f"  packed input_ids shape: {tuple(input_ids.shape)}")
    print(f"  block-diagonal mask shape: {tuple(block_keep.shape)}")
    print(f"  attend-allowed entries: {int(block_keep.sum())} of {block_keep.numel()}")
    print(f"  attend-allowed fraction: {int(block_keep.sum()) / block_keep.numel() * 100:.1f}%")
    packed_matches = []
    for pack_index, name, start, length in segments:
        # TODO 10: Slice this segment out of packed_out and compare it to its
        # standalone reference. The slice is
        # packed_out[pack_index, start:start + length]. Append the
        # torch.allclose result to packed_matches and replace `match` below.
        # Expect True for all 14 segments: the mask makes the pack exactly
        # equivalent to independent inference.
        got = packed_out[pack_index, start : start + length]
        match = False
        packed_matches.append(match)
        print(
            f"  pack {pack_index + 1} {name:<15} offset={start:>3} len={length:>3} match={match}"
        )
        print(
            f"[measured] {name}: packed-vs-standalone max abs diff "
            f"{float((standalone[name] - got).abs().max()):.3e}",
            file=sys.stderr,
        )
    print(f"  sequences matching standalone: {sum(packed_matches)} of {len(segments)}")
    print(f"  all match: {all(packed_matches)}")
    print()

    # TODO 11: The negative control. leaky_out is the same packed batch run with
    # only the padding mask, so tokens can attend across protein boundaries.
    # Fill leaky_matches with the torch.allclose results and leaky_rel with
    # relative_error(standalone[name], slice) for every segment. A correctness
    # test that cannot fail proves nothing, so this must come out False
    # everywhere.
    leaky_matches = []
    leaky_rel = []
    for pack_index, name, start, length in segments:
        got = leaky_out[pack_index, start : start + length]
        leaky_matches.append(True)
        leaky_rel.append(0.0)
    worst = max(leaky_rel)
    best = min(leaky_rel)

    print("--- part 2b: negative control, padding-only mask ---")
    print("  every real token can attend to every other real token in its pack")
    print(f"  sequences matching standalone: {sum(leaky_matches)} of {len(segments)}")
    print(f"  any match: {any(leaky_matches)}")
    print(f"  worst relative corruption: {worst * 100:.0f}%")
    print(f"  least affected sequence: {best * 100:.0f}%")
    print(f"  corruption above 1 percent everywhere: {best > 0.01}")
    print()
    for (pack_index, name, start, length), rel in zip(segments, leaky_rel):
        print(f"[measured] {name}: leaked relative error {rel:.6f}", file=sys.stderr)

    print("--- part 2c: position ids, on a block we control ---")
    print(f"  ESM-2 position embedding type: {config.position_embedding_type}")
    print("  rotary attention depends on i-j only, so segment offsets cancel")
    print("  the toy block below uses learned absolute positions instead")
    params = make_toy_params(tokenizer.vocab_size + 1, TOY_DIM, PACK_CAPACITY)
    reset_positions = segment_position_ids(segments, len(packs), PACK_CAPACITY)
    running_positions = torch.arange(PACK_CAPACITY).expand(len(packs), PACK_CAPACITY)

    with torch.inference_mode():
        toy_reset = toy_block(params, input_ids, reset_positions, block_additive)
        toy_running = toy_block(params, input_ids, running_positions, block_additive)
        toy_standalone = {}
        for name, length in items:
            ids = torch.tensor([encoded[name]])
            positions = torch.arange(length).unsqueeze(0)
            allow = torch.ones(1, 1, length, length)
            toy_standalone[name] = toy_block(params, ids, positions, to_additive(allow))[0]

    # TODO 12: Same comparison twice on the toy block, with the same correct
    # block-diagonal mask both times. toy_reset used per-segment position ids
    # and every segment should match. toy_running used continuous ids across
    # the pack and only the segments at offset 0 should match. Collect the
    # relative error for the offset > 0 segments in running_rel.
    reset_matches = []
    running_matches = []
    running_rel = []
    for pack_index, name, start, length in segments:
        reference = toy_standalone[name]
        reset_matches.append(False)
        running_matches.append(False)
        if start > 0:
            running_rel.append(0.0)

    print(f"  per-segment position ids: {sum(reset_matches)} of {len(segments)} match")
    print(f"  continuous position ids: {sum(running_matches)} of {len(segments)} match")
    print(f"  segments at a nonzero offset: {len(running_rel)}")
    print(f"  worst relative corruption from continuous ids: {max(running_rel) * 100:.0f}%")
    print()

    naive_rows = padded_rows(lengths, NAIVE_BATCH_SIZE)
    bucketed_rows = padded_rows(bucketed_lengths, NAIVE_BATCH_SIZE)
    dense_packed_rows = [PACK_CAPACITY] * len(packs)
    block_entries = score_entries([length for _, _, _, length in segments])
    mask_bytes = block_keep.numel() * block_keep.element_size()

    print("--- part 3: what packing costs and saves ---")
    print("  token slots processed")
    print(f"    naive padded: {naive_slots}")
    print(f"    length-bucketed: {bucketed_slots}")
    print(f"    packed: {packed_slots}")
    print(f"    useful: {useful}")
    print("  attention score entries, one per query-key pair per head per layer")
    print(f"    naive padded: {score_entries(naive_rows)}")
    print(f"    length-bucketed: {score_entries(bucketed_rows)}")
    print(f"    packed, dense kernel: {score_entries(dense_packed_rows)}")
    print(f"    packed, block-sparse kernel: {block_entries}")
    print(f"    one at a time, no padding: {score_entries(lengths)}")
    dense_entries = score_entries(dense_packed_rows)
    print(f"    packed dense vs block-sparse ideal: {dense_entries / block_entries:.2f}x more")
    print(f"    packed dense vs naive padded: {dense_entries / score_entries(naive_rows):.2f}x more")
    print(f"    packed dense vs length-bucketed: {dense_entries / score_entries(bucketed_rows):.2f}x more")
    print("  attention mask memory")
    print(f"    padding mask, float32: {padding_mask.numel() * padding_mask.element_size()} bytes")
    print(f"    block-diagonal mask, float32: {mask_bytes} bytes")
    print(f"    block-diagonal mask, bool: {block_keep.numel()} bytes")
    print(
        f"    same mask at capacity {BIG_CAPACITY} with {BIG_PACKS} packs, float32: "
        f"{BIG_PACKS * BIG_CAPACITY * BIG_CAPACITY * 4} bytes"
    )


if __name__ == "__main__":
    main()
