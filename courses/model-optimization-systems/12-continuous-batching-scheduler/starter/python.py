"""
Continuous batching over a real paged KV cache.

You will drive an actual torch KV cache through real attention decode steps
while requests join and leave the batch, then prove that batching did not change
any request's output.

Everything graded runs on CPU in float32 under seed 0 so your numbers match the
grader exactly. Wall-clock measurement goes to stderr, which is not graded.
"""

import bisect
import math
import sys
import time

import torch

N_KV_HEADS = 8
HEAD_DIM = 64
D_MODEL = N_KV_HEADS * HEAD_DIM
BLOCK_SIZE = 16
N_BLOCKS = 6
MAX_ACTIVE = 3
MAX_STEPS = 200

SWEEP_BLOCK_SIZES = [1, 8, 16, 32, 64]
SWEEP_TOTAL_SLOTS = 256

# Padding the batched attention to the longest active sequence changes the
# reduction order of the softmax and the P.V matmul, so agreement with a
# single-request replay is exact only up to float32 rounding.
RTOL = 1e-4
ATOL = 1e-5

REQUESTS = [
    {"id": "R0", "arrival": 0, "prompt": 10, "gen": 6},
    {"id": "R1", "arrival": 0, "prompt": 20, "gen": 12},
    {"id": "R2", "arrival": 1, "prompt": 6, "gen": 3},
    {"id": "R3", "arrival": 2, "prompt": 34, "gen": 8},
    {"id": "R4", "arrival": 4, "prompt": 12, "gen": 10},
    {"id": "R5", "arrival": 5, "prompt": 8, "gen": 4},
    {"id": "R6", "arrival": 14, "prompt": 6, "gen": 5},
    {"id": "R7", "arrival": 15, "prompt": 18, "gen": 6},
]


def blocks_needed(request: dict, block_size: int) -> int:
    total = request["prompt"] + request["gen"]
    return (total + block_size - 1) // block_size


def make_cache(n_blocks: int, block_size: int) -> dict:
    """Preallocate the whole KV pool up front, the way a server does at startup."""
    return {
        "k": torch.zeros(n_blocks, block_size, N_KV_HEADS, HEAD_DIM),
        "v": torch.zeros(n_blocks, block_size, N_KV_HEADS, HEAD_DIM),
        "free": list(range(n_blocks)),
        "table": {},
        "block_size": block_size,
        "n_blocks": n_blocks,
        "allocations": [],
    }


def cache_bytes(cache: dict) -> int:
    return (cache["k"].numel() + cache["v"].numel()) * cache["k"].element_size()


def allocate_block(cache: dict, rid: str) -> int:
    """Hand the lowest-numbered free physical block to rid and return it."""
    # TODO 1: Remove the lowest block id from cache["free"], append it to
    # cache["table"][rid], record (block, rid) in cache["allocations"] so the
    # program can report block recycling, and return the block id.
    # cache["free"] is kept sorted, so the lowest id is at index 0.
    raise NotImplementedError


def free_request(cache: dict, rid: str) -> None:
    """Return every block owned by rid to the free list.

    Do not zero the blocks. Stale keys are harmless as long as every read is
    bounded by the owning request's true length -- which is exactly the invariant
    the equivalence test at the end of this program checks.
    """
    # TODO 2: Pop rid's entry out of cache["table"] and insert each of its
    # blocks back into cache["free"], keeping that list sorted.
    # bisect.insort does the sorted insert in one call.
    # If you forget this step the free list drains, no further request can be
    # admitted, and run_scheduler raises after MAX_STEPS.
    raise NotImplementedError


def ensure_capacity(cache: dict, rid: str, pos: int) -> None:
    """Grow rid's block table on demand until logical position pos has a slot."""
    while len(cache["table"][rid]) * cache["block_size"] <= pos:
        allocate_block(cache, rid)


def write_kv(cache: dict, rid: str, pos: int, k: torch.Tensor, v: torch.Tensor) -> None:
    """Write one token's K/V, shape (N_KV_HEADS, HEAD_DIM), at logical position pos."""
    # TODO 3: Translate the logical position into physical storage.
    #   block = cache["table"][rid][pos // block_size]
    #   slot  = pos % block_size
    # Then store k into cache["k"][block, slot] and v into cache["v"][block, slot].
    # This is the only place where the block table turns a sequence index into
    # an address, so an error here corrupts one request's history silently.
    raise NotImplementedError


def gather_kv(cache: dict, rid: str, length: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Collect logical positions [0, length) for rid into contiguous tensors.

    Returns two tensors of shape (length, N_KV_HEADS, HEAD_DIM).
    """
    # TODO 4: A request's history is spread over the blocks in its block table,
    # in logical order. Work out how many blocks hold the first `length` tokens
    # (ceiling division), index the cache with that list of block ids, which
    # gives (n_used, block_size, N_KV_HEADS, HEAD_DIM), flatten the first two
    # dimensions, and trim to exactly `length` rows.
    # Trimming matters: the final block is usually only partly filled, and the
    # unused slots may hold another request's old keys.
    raise NotImplementedError


def decode_step(
    cache: dict,
    active_ids: list[str],
    lengths: list[int],
    queries: torch.Tensor,
) -> tuple[torch.Tensor, int]:
    """One batched multi-head attention decode step reading from the paged cache.

    queries: (B, N_KV_HEADS, HEAD_DIM), one query per active request.
    lengths: cached length per active request, including the token just written.
    Returns ((B, D_MODEL) outputs, number of block-table entries read).
    """
    batch = len(active_ids)
    max_len = max(lengths)

    keys = torch.zeros(batch, max_len, N_KV_HEADS, HEAD_DIM)
    values = torch.zeros(batch, max_len, N_KV_HEADS, HEAD_DIM)
    mask = torch.zeros(batch, max_len, dtype=torch.bool)
    block_reads = 0

    for i, rid in enumerate(active_ids):
        length = lengths[i]
        # TODO 5a: gather this request's K/V, copy them into keys[i, :length]
        # and values[i, :length], and set mask[i, :length] = True. Rows beyond
        # `length` stay masked off; they belong to a different request or to no
        # request at all.
        block_reads += (length + cache["block_size"] - 1) // cache["block_size"]

    # TODO 5b: batched scaled dot-product attention with one query per request.
    #   scores = einsum("bhd,blhd->bhl", queries, keys) / sqrt(HEAD_DIM)
    #   scores = scores.masked_fill(~mask.unsqueeze(1), float("-inf"))
    #   probs  = torch.softmax(scores, dim=-1)
    #   out    = einsum("bhl,blhd->bhd", probs, values)
    # No causal mask is needed: the cache only ever holds past tokens plus the
    # current one. Reshape the result to (batch, D_MODEL) before returning it.
    raise NotImplementedError


def admit(cache: dict, request: dict, qkv: dict, block_size: int) -> dict:
    """Prefill the prompt into the cache and return the active-request record."""
    rid = request["id"]
    cache["table"][rid] = []
    _, k, v = qkv[rid]
    for pos in range(request["prompt"]):
        ensure_capacity(cache, rid, pos)
        write_kv(cache, rid, pos, k[pos], v[pos])
    return {
        "id": rid,
        "need": blocks_needed(request, block_size),
        "length": request["prompt"],
        "remaining": request["gen"],
        "outputs": [],
    }


def run_scheduler(requests: list[dict], qkv: dict, n_blocks: int, block_size: int, max_active: int) -> dict:
    """Continuous batching: admit whenever a slot and enough blocks are free."""
    cache = make_cache(n_blocks, block_size)
    waiting = [dict(r) for r in requests]
    active: list[dict] = []
    outputs: dict[str, torch.Tensor] = {}
    finished: dict[str, int] = {}
    timeline: list[tuple[int, list[str]]] = []

    peak_active = 0
    peak_blocks = 0
    peak_step = 0
    peak_live_tokens = 0
    peak_table_entries = 0
    block_reads = 0
    slot_sum = 0
    live_sum = 0
    step = 0

    while waiting or active:
        if step > MAX_STEPS:
            raise RuntimeError(
                "scheduler made no progress: blocks are probably leaking on completion"
            )
        i = 0
        while i < len(waiting) and len(active) < max_active:
            request = waiting[i]
            # Blocks still owed to already-admitted requests must stay reserved,
            # or on-demand growth could fail mid-generation.
            reserved = sum(a["need"] - len(cache["table"][a["id"]]) for a in active)
            fits = len(cache["free"]) - reserved >= blocks_needed(request, block_size)
            if request["arrival"] <= step and fits:
                waiting.pop(i)
                active.append(admit(cache, request, qkv, block_size))
            else:
                i += 1

        if not active:
            step += 1
            continue

        active_ids = [a["id"] for a in active]
        timeline.append((step, active_ids))
        peak_active = max(peak_active, len(active))

        lengths = []
        queries = []
        for a in active:
            pos = a["length"]
            ensure_capacity(cache, a["id"], pos)
            q, k, v = qkv[a["id"]]
            write_kv(cache, a["id"], pos, k[pos], v[pos])
            a["length"] = pos + 1
            lengths.append(a["length"])
            queries.append(q[pos])

        out, reads = decode_step(cache, active_ids, lengths, torch.stack(queries))
        block_reads += reads
        for i, a in enumerate(active):
            a["outputs"].append(out[i])
            a["remaining"] -= 1

        blocks_in_use = sum(len(b) for b in cache["table"].values())
        slot_sum += blocks_in_use * block_size
        live_sum += sum(lengths)
        if blocks_in_use > peak_blocks:
            peak_blocks = blocks_in_use
            peak_step = step
            peak_live_tokens = sum(lengths)
            peak_table_entries = blocks_in_use

        for a in list(active):
            if a["remaining"] == 0:
                outputs[a["id"]] = torch.stack(a["outputs"])
                finished[a["id"]] = step + 1
                free_request(cache, a["id"])
                active.remove(a)

        step += 1

    return {
        "cache": cache,
        "outputs": outputs,
        "finished": finished,
        "timeline": timeline,
        "peak_active": peak_active,
        "peak_blocks": peak_blocks,
        "peak_step": peak_step,
        "peak_live_tokens": peak_live_tokens,
        "peak_table_entries": peak_table_entries,
        "block_reads": block_reads,
        "slot_sum": slot_sum,
        "live_sum": live_sum,
        "steps": step,
    }


def replay_single(request: dict, qkv: dict, block_size: int) -> torch.Tensor:
    """Run one request alone through a clean cache. This is the trusted reference.

    Returns the (gen, D_MODEL) stack of decode outputs.
    """
    # TODO 6: Build a fresh cache holding exactly blocks_needed(request,
    # block_size) blocks, call admit() to prefill the prompt, then run
    # request["gen"] decode steps for this request alone:
    #   pos = current length; ensure_capacity; write_kv the token at pos;
    #   advance the length; decode_step with a batch of one, passing
    #   q[pos].unsqueeze(0) as the query.
    # Collect the (D_MODEL,) output of each step and torch.stack them.
    # Nothing else may touch this cache -- that is what makes it trustworthy.
    raise NotImplementedError


def fragmentation(blocks_in_use: int, block_size: int, live_tokens: int) -> tuple[int, int, float]:
    """Return (allocated_slots, wasted_slots, wasted_percent)."""
    # TODO 7: Allocated slots is blocks_in_use * block_size. Wasted slots are
    # the allocated slots not holding a live token. Return the count and the
    # waste as a percentage of allocated slots.
    raise NotImplementedError


def token_bytes(n_tokens: int) -> int:
    return n_tokens * N_KV_HEADS * HEAD_DIM * 2 * 4


def build_projections() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    scale = 1.0 / math.sqrt(D_MODEL)
    wq = torch.randn(D_MODEL, D_MODEL) * scale
    wk = torch.randn(D_MODEL, D_MODEL) * scale
    wv = torch.randn(D_MODEL, D_MODEL) * scale
    return wq, wk, wv


def build_qkv(requests: list[dict], wq, wk, wv) -> dict:
    """Project each request's hidden states once so every run sees identical inputs."""
    qkv = {}
    for request in requests:
        total = request["prompt"] + request["gen"]
        x = torch.randn(total, D_MODEL)
        shape = (total, N_KV_HEADS, HEAD_DIM)
        qkv[request["id"]] = (
            (x @ wq).reshape(shape),
            (x @ wk).reshape(shape),
            (x @ wv).reshape(shape),
        )
    return qkv


def recycled_blocks(cache: dict) -> list[tuple[int, list[str]]]:
    owners: dict[int, list[str]] = {}
    for block, rid in cache["allocations"]:
        owners.setdefault(block, []).append(rid)
    return [(block, rids) for block, rids in sorted(owners.items()) if len(rids) > 1]


def main() -> None:
    torch.manual_seed(0)
    started = time.perf_counter()

    with torch.inference_mode():
        wq, wk, wv = build_projections()
        qkv = build_qkv(REQUESTS, wq, wk, wv)

        print("=== Continuous batching over a real paged KV cache ===")
        print(f"n_kv_heads: {N_KV_HEADS}")
        print(f"head_dim: {HEAD_DIM}")
        print(f"d_model: {D_MODEL}")
        print(f"block_size: {BLOCK_SIZE}")
        print(f"n_blocks: {N_BLOCKS}")
        print(f"max_active: {MAX_ACTIVE}")
        print()

        probe = make_cache(N_BLOCKS, BLOCK_SIZE)
        print(f"cache_k shape: {tuple(probe['k'].shape)}")
        print(f"cache dtype: {probe['k'].dtype}")
        print(f"total cache slots: {N_BLOCKS * BLOCK_SIZE}")
        print(f"total cache bytes: {cache_bytes(probe)}")
        print()

        print("--- workload ---")
        for request in REQUESTS:
            total = request["prompt"] + request["gen"]
            print(
                f"  {request['id']} arrival={request['arrival']} "
                f"prompt={request['prompt']} gen={request['gen']} "
                f"total={total} blocks_needed={blocks_needed(request, BLOCK_SIZE)}"
            )
        print()

        run = run_scheduler(REQUESTS, qkv, N_BLOCKS, BLOCK_SIZE, MAX_ACTIVE)

        print("--- decode timeline (active requests before each step) ---")
        for step, active_ids in run["timeline"]:
            print(f"  step {step:2d}: active={','.join(active_ids)}")
        print(f"  decode steps: {run['steps']}")
        finished = run["finished"]
        print("  finished: " + " ".join(f"{rid}:{finished[rid]}" for rid in sorted(finished)))
        print()

        print("--- block table activity ---")
        print(f"peak concurrent requests: {run['peak_active']}")
        print(f"peak blocks in use: {run['peak_blocks']}")
        print(f"total block allocations: {len(run['cache']['allocations'])}")
        recycled = recycled_blocks(run["cache"])
        print(f"recycled physical blocks: {len(recycled)}")
        for block, rids in recycled:
            print(f"  block {block}: {' -> '.join(rids)}")
        print(f"free blocks at end: {len(run['cache']['free'])}")
        print()

        allocated, wasted, waste_pct = fragmentation(
            run["peak_blocks"], BLOCK_SIZE, run["peak_live_tokens"]
        )
        print(f"--- memory at peak block usage (step {run['peak_step']}) ---")
        print(f"blocks in use: {run['peak_blocks']}")
        print(f"block table entries: {run['peak_table_entries']}")
        print(f"allocated slots: {allocated}")
        print(f"live tokens: {run['peak_live_tokens']}")
        print(f"total cache bytes: {cache_bytes(run['cache'])}")
        print(f"allocated bytes: {token_bytes(allocated)}")
        print(f"live token bytes: {token_bytes(run['peak_live_tokens'])}")
        print(f"wasted slots: {wasted}")
        print(f"internal fragmentation: {waste_pct:.3f}%")
        mean_waste = 100.0 * (1.0 - run["live_sum"] / run["slot_sum"])
        print(f"mean internal fragmentation over all steps: {mean_waste:.3f}%")
        print(f"total block-table reads during gather: {run['block_reads']}")
        print()

        print("--- batched vs individual equivalence ---")
        print(f"tolerance: rtol={RTOL:.0e} atol={ATOL:.0e}")
        all_match = True
        for request in REQUESTS:
            rid = request["id"]
            batched = run["outputs"][rid]
            alone = replay_single(request, qkv, BLOCK_SIZE)
            max_diff = (batched - alone).abs().max().item()
            match = torch.allclose(batched, alone, rtol=RTOL, atol=ATOL)
            all_match = all_match and match
            print(
                f"  {rid} out shape={tuple(batched.shape)} "
                f"max_abs_diff={max_diff:.5f} allclose={match}"
            )
        print(f"all requests match individual replay: {all_match}")
        print()

        print(f"--- block size sweep (total slots held at {SWEEP_TOTAL_SLOTS}) ---")
        for block_size in SWEEP_BLOCK_SIZES:
            n_blocks = (SWEEP_TOTAL_SLOTS + block_size - 1) // block_size
            sweep = run_scheduler(REQUESTS, qkv, n_blocks, block_size, MAX_ACTIVE)
            pct = 100.0 * (1.0 - sweep["live_sum"] / sweep["slot_sum"])
            equal = all(
                torch.allclose(
                    sweep["outputs"][r["id"]],
                    replay_single(r, qkv, block_size),
                    rtol=RTOL,
                    atol=ATOL,
                )
                for r in REQUESTS
            )
            print(
                f"  B={block_size:<3d} n_blocks={n_blocks:<4d} "
                f"peak_blocks={sweep['peak_blocks']:<4d} "
                f"table_entries={sweep['peak_table_entries']:<4d} "
                f"frag={pct:6.3f}% "
                f"block_reads={sweep['block_reads']:<5d} "
                f"equiv={equal}"
            )
        print()

    elapsed = (time.perf_counter() - started) * 1000.0
    print(f"[measured] total wall clock: {elapsed:.3f} ms", file=sys.stderr)


if __name__ == "__main__":
    main()
