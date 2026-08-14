# Solution walkthrough

## The cache is a dict of tensors plus a free list

`make_cache` preallocates both K and V as
`(n_blocks, block_size, n_kv_heads, head_dim)` zeros. The free list starts as
`list(range(n_blocks))`, so the first allocation always hands out physical
block 0. Keeping that list sorted with `bisect.insort` on free is what makes
the recycling trace deterministic: the lowest-numbered free block is always
next.

`write_kv` is two integer divisions and two assignments. `gather_kv` is the
operation that has to be right. Selecting `blocks[:n_used]`, reshaping to
concatenate them, and slicing to `length` drops the unused tail of the last
block. Returning the un-sliced tensor would attend over stale keys from a
previous owner — and because blocks are not zeroed, those keys are real
numbers, not zeros.

## Why the workload recycles

Six physical blocks and `MAX_ACTIVE = 3` is tight on purpose. `R1` needs two
blocks and `R3` needs three; together with anyone else they fill the pool.
When `R0` and `R2` complete, their blocks go back on the free list and are
immediately reused. The printed ownership of block 0 — `R0 -> R5 -> R4` — is
the evidence that a physical region held three unrelated requests' K/V over
the run. Any indexing bug that confused those owners would have shown up in
the equivalence test.

The scheduler also refuses to admit a request unless the free list, minus
blocks already reserved for in-flight growth, can cover that request's
worst-case footprint. Without the reservation, `R3` would be admitted into a
pool that later cannot give it a third block, and generation would fail
mid-request.

## Equivalence is exact at printed precision

Each request is replayed alone through a clean cache with the same projected
Q/K/V. The batched path pads to the longest *currently active* sequence, so
the softmax is a reduction over a slightly different set of finite-versus-`-inf`
scores and the matmul association can differ by a few ulps. In this workload
every `max_abs_diff` prints as `0.00000` at five decimals, well inside the
`1e-5` absolute tolerance. That is a statement about this shape, not a
guarantee for every shape — which is why the check is `allclose` rather than
`equal`.

The interesting failure modes are not ulps. Gathering `length+1` rows, skipping
`free_request`, or forgetting the pad mask all move the output by $O(1)$ and
flip `allclose` to `False`. The test has teeth because the workload recycles
blocks *and* the blocks keep their previous contents.

## The sweep is the quantitative payoff

Holding the pool at 256 slots and varying $B$:

| $B$ | Peak blocks | Internal fragmentation | Block-table reads | Equivalence |
|---:|---:|---:|---:|---|
| 1 | 92 | 0.000% | 1122 | True |
| 8 | 13 | 13.426% | 162 | True |
| 16 | 7 | 25.399% | 94 | True |
| 32 | 4 | 43.448% | 62 | True |
| 64 | 3 | 67.535% | 54 | True |

Block size 1 is a perfect allocator and a terrible gather. Block size 64 is a
cheap gather that wastes two-thirds of every allocated block on this traffic
mix. Production stacks live in the middle because both extremes are real
costs. Equivalence holding in every row is the reminder that the cache
abstraction is independent of $B$ — only the economics change.

## What this still leaves out

The lab is one layer, one decode-only loop, no prefix sharing, no prefill
chunks, and no copy-on-write. Real PagedAttention also has to:

- share immutable prefix blocks across requests that start with the same
  tokens;
- copy a block the moment a shared prefix diverges;
- schedule prefill chunks against decode steps without stalling either;
- page blocks to CPU under memory pressure.

Those are all elaborations of the same three primitives you implemented:
allocate a block, write a slot, gather a logical span. The equivalence test is
the thing that has to keep passing as each of those is added.
