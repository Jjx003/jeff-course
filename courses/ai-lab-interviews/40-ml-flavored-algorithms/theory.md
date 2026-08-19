# The Five Patterns

## Top-k with a heap

```python
heap = []                       # min-heap of (value, index)
for i, value in enumerate(logits):
    if len(heap) < k:
        heapq.heappush(heap, (value, i))
    elif value > heap[0][0]:
        heapq.heapreplace(heap, (value, i))
```

$O(n\log k)$ time, $O(k)$ space, against $O(n\log n)$ and $O(n)$ for a full sort. On a 128k-token vocabulary at every decoding step, that difference is the whole reason `torch.topk` exists rather than `torch.sort`.

`heapreplace` rather than a pop followed by a push: one sift instead of two.

**Follow-ups to have ready:**

- *"What if you only need the set, not the order?"* Quickselect: $O(n)$ average.
- *"What if the stream does not fit in memory?"* The heap already handles it — it holds $O(k)$ regardless of $n$.
- *"Ties?"* Decide and say so. Here they break by index, which makes the output deterministic and testable.

## Interval merging

Sort by start, then sweep, extending the last interval when the next one overlaps.

The correctness argument is short and worth giving: after sorting by start, any interval that overlaps an earlier one must overlap the *most recent* merged interval, because the merged interval's end is the maximum end seen so far. So you only ever need to compare against `merged[-1]`.

Note the half-open convention: `[0,5)` and `[5,9)` merge to `[0,9)` because position 5 is where one ends and the other begins. State your convention; interviewers accept either but not silence.

## Sequence packing

Bin packing is NP-hard, so the answer is a greedy heuristic, and saying that immediately is the right move.

**First-fit-decreasing** — sort by length descending, place each into the first bin with room — is within about 22% of optimal in the worst case and much better than that in practice. The reason for the descending sort: large items are the hard ones to place, so place them while bins are still empty.

The script reports the padding waste both ways. On the sample input, one sequence per bin wastes 67% of the token budget; packing brings it to 23%. That is compute you are otherwise spending on padding, and it is why every serious training pipeline packs.

## Binary search on the answer

The pattern people miss, and the one with the most ML applications.

If `check(x)` is monotone — true for all $x$ up to some boundary and false after — then you can binary search over $x$ even when $x$ is not an index into anything.

```python
while lo < hi:
    mid = (lo + hi + 1) // 2      # +1 so mid never equals lo when hi = lo+1
    if check(mid): lo = mid
    else: hi = mid - 1
```

The `+1` matters. Without it, `mid` equals `lo` when `hi == lo + 1`, `check` passes, `lo` does not move, and you loop forever. That specific infinite loop is one of the most common binary-search bugs in interviews.

**Where it applies here:** largest batch size that fits in memory, minimum GPUs to serve a load, largest context length within a latency budget, threshold achieving a target recall. All monotone, all expensive to check, all $O(\log R)$ checks.

## Sliding window

Maintain a `deque` of the window and a `Counter` of its contents. Add on the right, evict on the left when the window overflows, and delete zero-count keys so the counter's size *is* the distinct count.

Deleting zero entries is the detail. Without it, `len(counts)` counts tokens that have left the window, and the bug only shows on inputs where a token leaves and does not return — which random testing finds and hand-picked cases often do not.

Every element enters once and leaves once, so total work is $O(n)$ despite the nested structure. Being able to give that amortization argument is a standard follow-up.

# Testing by Fuzzing

The script's approach, and the one to bring into interviews:

1. Write the obvious slow version. For `rolling_distinct` that is `len(set(tokens[i:i+w]))` per position — $O(nw)$ and clearly correct.
2. Generate random inputs across the interesting range, including degenerate sizes.
3. Assert the fast and slow versions agree.
4. Add hand-picked edge cases for things random generation is unlikely to produce.

For problems with no easy reference — like packing, where the greedy answer is not unique — assert the **invariants** instead: every item placed exactly once, no bin over budget. That is the right generalization, and it is what the script does.

Saying "let me fuzz this against a brute force" when asked how you would test is a strong answer, because it is what you would actually do.
