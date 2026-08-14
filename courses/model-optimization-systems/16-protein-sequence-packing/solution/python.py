"""
Reference solution for module 16.
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
    total = 0
    for start in range(0, len(lengths), batch_size):
        group = lengths[start : start + batch_size]
        total += len(group) * max(group)
    return total


def padded_rows(lengths, batch_size: int):
    rows = []
    for start in range(0, len(lengths), batch_size):
        group = lengths[start : start + batch_size]
        rows.extend([max(group)] * len(group))
    return rows


def first_fit_decreasing(items, capacity: int):
    packs = []
    used = []
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
    return packs


def build_packed_batch(packs, encoded, capacity: int, pad_id: int):
    input_ids = torch.full((len(packs), capacity), pad_id, dtype=torch.long)
    padding_mask = torch.zeros(len(packs), capacity)
    segments = []
    for pack_index, pack in enumerate(packs):
        offset = 0
        for name, length in pack:
            input_ids[pack_index, offset : offset + length] = torch.tensor(encoded[name])
            padding_mask[pack_index, offset : offset + length] = 1.0
            segments.append((pack_index, name, offset, length))
            offset += length
    return input_ids, padding_mask, segments


def block_diagonal_keep_mask(segments, n_packs: int, capacity: int) -> torch.Tensor:
    keep = torch.zeros(n_packs, 1, capacity, capacity)
    for pack_index, _, start, length in segments:
        keep[pack_index, 0, start : start + length, start : start + length] = 1.0
    return keep


def padding_keep_mask(padding_mask: torch.Tensor) -> torch.Tensor:
    return padding_mask[:, None, None, :].expand(-1, 1, padding_mask.shape[1], -1).contiguous()


def to_additive(keep: torch.Tensor) -> torch.Tensor:
    return (1.0 - keep) * torch.finfo(torch.float32).min


def segment_position_ids(segments, n_packs: int, capacity: int) -> torch.Tensor:
    position_ids = torch.zeros(n_packs, capacity, dtype=torch.long)
    for pack_index, _, start, length in segments:
        position_ids[pack_index, start : start + length] = torch.arange(length)
    return position_ids


def encode_packed(model, input_ids: torch.Tensor, padding_mask: torch.Tensor, additive: torch.Tensor):
    """Run ESM-2 with an arbitrary 4D additive attention mask.

    EsmModel.forward cannot express this: it rejects a 4D mask outright and
    crashes on a 3D one, because the embedding layer reuses the same tensor as a
    per-token padding mask. So the padding mask goes to the embeddings and the
    block-diagonal mask goes straight to the encoder.
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
    """One self-attention block with learned absolute position embeddings."""
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
    return sum(length * length for length in rows)


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

    padded_matches = [
        torch.allclose(standalone[name], batched[row, :length], atol=ATOL)
        for row, (name, length) in enumerate(items)
    ]

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
        got = packed_out[pack_index, start : start + length]
        match = torch.allclose(standalone[name], got, atol=ATOL)
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

    leaky_matches = []
    leaky_rel = []
    for pack_index, name, start, length in segments:
        got = leaky_out[pack_index, start : start + length]
        leaky_matches.append(torch.allclose(standalone[name], got, atol=ATOL))
        leaky_rel.append(relative_error(standalone[name], got))
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

    reset_matches = []
    running_matches = []
    running_rel = []
    for pack_index, name, start, length in segments:
        reference = toy_standalone[name]
        reset_matches.append(
            torch.allclose(reference, toy_reset[pack_index, start : start + length], atol=ATOL)
        )
        got = toy_running[pack_index, start : start + length]
        running_matches.append(torch.allclose(reference, got, atol=ATOL))
        if start > 0:
            running_rel.append(relative_error(reference, got))

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
