# Continuous batching over a paged KV cache

The previous module argued that a serving system is mostly a KV cache plus a
scheduler. This lab builds both against real tensors and then checks the
property that actually matters: **a request batched alongside others must
produce the same output it would have produced alone.**

If that property fails, the server is silently wrong. The bug is nearly always
in cache indexing — a stale slot, an off-by-one in sequence length, a block-table
entry that still belongs to a finished request, or attending over another
request's keys. The exercise is designed so those bugs have somewhere to hide:
requests join and leave mid-flight, and freed physical blocks are reused by later
requests without being zeroed.

Everything runs on CPU in float32 under `torch.manual_seed(0)`. Graded output
is deterministic. Wall-clock timing is printed to **stderr**, which is streamed
in the session log but is not graded.

## The cache

The pool is preallocated at startup, the way a real server does it:

```text
k, v: (n_blocks, block_size, n_kv_heads, head_dim)   # 6 × 16 × 8 × 64
```

That is 96 slots and `393216` bytes. A *block table* maps each active request to
the physical block indices it currently owns. Logical position `pos` lives at:

$$
\text{block} = \text{table}[\lfloor \text{pos} / B \rfloor], \qquad
\text{slot} = \text{pos} \bmod B
$$

where $B$ is the block size. Growing a sequence means appending a free physical
block to its table. Completing a sequence means returning every one of its
blocks to the free list. The blocks are **not** zeroed on free. Stale keys are
harmless if and only if every subsequent read is bounded by the new owner's true
length — which is exactly what the equivalence test checks.

You implement `allocate_block`, `free_request`, `write_kv`, and `gather_kv`.
`gather_kv` is the one that turns a scattered history back into a contiguous
`(length, n_kv_heads, head_dim)` tensor for attention.

## The decode step

`decode_step` runs one batched multi-head attention over the active set. Each
active request contributes one query; its keys and values are gathered from the
cache and padded to the longest active sequence. A boolean mask keeps the pad
slots out of the softmax. The attention is causal by construction: the cache
holds only past tokens.

The scheduler loop is given. At each step it:

1. admits waiting requests that have arrived and for which enough free blocks
   remain (counting blocks already reserved for in-flight growth);
2. writes each active request's next K/V into the cache;
3. runs `decode_step`;
4. retires finished requests and frees their blocks.

The workload is eight requests with staggered arrivals and mixed prompt/decode
lengths, plus a `MAX_ACTIVE` of 3 and only 6 physical blocks. That combination
forces recycling: five physical blocks are reused by later requests, and block 0
is owned by `R0`, then `R5`, then `R4` over the course of the run. If the
schedule never recycled a block, the most common class of bug would not be
caught.

## The equivalence test

After the scheduled run, each request is replayed **alone** through a clean
cache with the same projections and the same hidden states. Compare the
per-request output tensors with `torch.allclose`. Print the max absolute
difference per request and an overall boolean.

The batched path pads to the longest active sequence, so the softmax reduction
order can differ from the single-request path by a few ulps. The starter's
tolerance (`rtol=1e-4`, `atol=1e-5`) is sized for that. A real indexing bug is
orders of magnitude larger: attending over a stale key from a previous owner
moves the output by $O(1)$, not $10^{-6}$.

## Fragmentation and the block-size sweep

At peak block usage, report allocated slots versus live tokens. The difference
is *internal fragmentation*: space reserved inside a partially filled last
block. Then sweep block sizes `{1, 8, 16, 32, 64}` at a fixed 256-slot pool.

Small blocks waste almost nothing and need a larger block table plus more gather
work. Large blocks waste a lot on the last block of every request. That is the
tradeoff PagedAttention exists to manage, and the sweep makes it quantitative:
block size 1 reports `0.000%` fragmentation and `1122` block-table reads; block
size 64 reports `67.535%` fragmentation and `54` reads. Equivalence must hold at
every size.

Do not change the starter constants or the output labels. The grader checks
printed stdout.

## Recap

You now have a paged KV cache, a continuous-batching scheduler, and a proof that
batching did not change any request's output — including after physical blocks
were recycled through three different owners. The next module is about
speculative decoding, which tries to spend those same decode steps on more than
one token at a time.
