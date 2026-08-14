# Hints

Work in TODO order. Get `write_kv` and `gather_kv` round-tripping a single
request before you look at the scheduler: if gather is wrong, every later
number is noise.

## Physical addressing

Logical position `pos` of a request whose block table is `table` and whose
block size is `B` lives at:

```python
block = table[pos // B]
slot  = pos % B
cache["k"][block, slot] = k    # k has shape (n_kv_heads, head_dim)
```

`ensure_capacity` already grows the table until that index is valid, so
`write_kv` should not allocate. If you find yourself calling `allocate_block`
from `write_kv`, the capacity invariant is already broken and you are hiding it.

## Gathering across block boundaries

A request of length 20 with $B = 16$ occupies two blocks. The first is full;
the second holds 4 live tokens and 12 stale-or-zero slots. `gather_kv` has to
return *exactly* 20 rows. The clean way:

```python
n_used = (length + block_size - 1) // block_size
keys = cache["k"][blocks[:n_used]].reshape(-1, N_KV_HEADS, HEAD_DIM)
return keys[:length], values[:length]
```

`reshape(-1, ...)` concatenates the selected blocks in table order. The final
slice drops the unused tail of the last block. Returning the un-sliced tensor
is the off-by-padding bug: the decode step then attends over 12 extra keys that
belong to whoever last owned that physical block.

## Freeing without zeroing

```python
for block in cache["table"].pop(rid):
    bisect.insort(cache["free"], block)
```

`bisect.insort` keeps the free list sorted so `allocate_block` can always pop
index 0 and hand out the lowest-numbered block. The lab's recycling report
depends on that deterministic choice; a stack (`pop()` from the end) still
works functionally but changes which blocks get reused, and the expected
output will not match.

Do not zero `cache["k"][block]`. The equivalence test is supposed to survive
stale leftovers. Zeroing would let a length bug pass by accident.

## The batched decode step

Pad to `max(lengths)`, copy each request's gathered K/V into its row, and mask
the pad:

```python
scores = torch.einsum("bhd,blhd->bhl", queries, keys) / math.sqrt(HEAD_DIM)
scores = scores.masked_fill(~mask.unsqueeze(1), float("-inf"))
probs = torch.softmax(scores, dim=-1)
out = torch.einsum("bhl,blhd->bhd", probs, values)
```

`mask` is `(batch, max_len)` and true on live tokens. `unsqueeze(1)` broadcasts
it over the heads. Forgetting the mask is a real bug and the equivalence test
will catch it — padded zeros in the keys are not the same as masked-out keys,
because a zero key still produces a finite score.

## Common mistakes

- Using `pos % n_blocks` instead of `pos % block_size` for the slot. The two
  coincide only when they are equal.
- Gathering `n_used * block_size` rows instead of `length` rows.
- Returning freed blocks with `append` instead of `insort`, which changes the
  recycling order and the printed block-ownership trace.
- Zeroing blocks on free "to be safe."
- Forgetting to `free_request` on completion. The scheduler then leaks, hits
  `MAX_STEPS`, and raises.
- Comparing batched and solo outputs with `torch.equal`. Padding changes the
  softmax reduction order by a few ulps; `allclose` is the right check.
- Admitting a request whenever `len(active) < MAX_ACTIVE` without reserving
  blocks for in-flight growth. The given scheduler already does this; do not
  "simplify" it.

## Sanity checks

- `cache_k shape` is `(6, 16, 8, 64)` and `total cache bytes` is `393216`.
- The timeline starts `R0,R1` at step 0, admits `R2` at step 1, and later shows
  `R4` running alone at steps 12–13 and 21. If `R3` appears before step 4, the
  block reservation is not holding.
- `finished` is `R0:6 R1:12 R2:4 R3:12 R4:22 R5:10 R6:19 R7:21`.
- Five physical blocks are recycled. Block 0's owners are `R0 -> R5 -> R4`.
- Peak usage is 6 blocks, 75 live tokens, `21.875%` internal fragmentation.
- All eight `allclose` flags are `True` and every `max_abs_diff` prints as
  `0.00000`.
- The sweep's `equiv` column is `True` at every block size. Fragmentation is
  `0.000%` at $B=1$ and `67.535%` at $B=64`.

## Going deeper

- Inject an off-by-one in `gather_kv` (`return keys[:length+1]`) and watch the
  equivalence test fail. Then free a request without returning its blocks and
  watch the scheduler raise at `MAX_STEPS`. Both are worth seeing once.
- Replace `insort` with `append` and re-run. Equivalence still holds — the
  cache is still correct — but the recycling trace changes. Correctness and
  determinism are different properties.
- Track *external* fragmentation under a contiguous allocator: give each
  request one span of `blocks_needed` adjacent slots and refuse to admit when
  no such span exists. With this workload the contiguous allocator will stall
  where the paged one does not.

## References

- Kwon et al., *Efficient Memory Management for Large Language Model Serving
  with PagedAttention*, SOSP 2023. The vLLM paper; block tables, copy-on-write
  prefixes, and the internal-fragmentation argument all originate here.
- Yu et al., *Orca: A Distributed Serving System for Transformer-Based
  Generative Models*, OSDI 2022. Continuous batching (iteration-level
  scheduling) as a serving policy, before paged cache made it memory-safe at
  scale.
- Zhong et al., *DistServe: Disaggregating Prefill and Decoding for
  Goodput-optimized Large Language Model Serving*, OSDI 2024. Why mixing
  prefill and decode on the same replica is its own scheduling problem.
