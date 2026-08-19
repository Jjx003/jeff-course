# The Patterns That Matter

## Hash maps and sets

The most common tool by a distance, and the one to reach for whenever a problem involves "have I seen this before" or "how many of each".

In an ML context: building a vocabulary from a corpus, counting token frequencies, deduplicating documents by exact hash, memoizing tokenizer results.

The interview-relevant nuance is what happens when the set does not fit in memory. The answers are a Bloom filter for approximate membership with no false negatives, or MinHash/LSH for near-duplicate detection. Knowing those two names turns a routine answer into a good one.

## Top-k with a heap

```python
import heapq
# k largest: maintain a MIN-heap of size k
heap = []
for value in stream:
    if len(heap) < k:
        heapq.heappush(heap, value)
    elif value > heap[0]:
        heapq.heapreplace(heap, value)
```

$O(n\log k)$ rather than $O(n\log n)$ for a full sort, and $O(k)$ memory rather than $O(n)$ — which is what makes it work on a stream.

**The counterintuitive bit, and the follow-up question:** for the $k$ *largest* you use a *min*-heap, because you need cheap access to the smallest of your current best $k$ in order to evict it.

**Where this is literally the ML answer:** top-k sampling over a 128k-token vocabulary. Sorting the whole vocabulary each step is wasteful; `torch.topk` does exactly this. A follow-up worth knowing: quickselect gives $O(n)$ average time if you only need the set and not the order.

## Two pointers and sliding window

The template that solves most "longest/shortest subarray with property X" problems:

```python
left = 0
for right, item in enumerate(items):
    add(item)
    while not valid():
        remove(items[left]); left += 1
    best = max(best, right - left + 1)
```

Every element enters and leaves once, so it is $O(n)$ despite the nested loop — and being able to say *why* it is linear is a common follow-up.

In ML: rolling statistics over a token stream, sliding-window attention spans, chunking a document into overlapping windows for retrieval.

## Binary search on the answer

The pattern people miss. If you can *check* whether a candidate answer works in $O(n)$, and the check is monotone in the candidate, binary search over answers gives $O(n\log R)$.

```python
lo, hi = min_possible, max_possible
while lo < hi:
    mid = (lo + hi) // 2
    if feasible(mid): hi = mid
    else: lo = mid + 1
```

Directly applicable: *"what is the largest batch size that fits in memory?"*, *"what is the smallest number of GPUs that serves this load?"*, *"what threshold gives at least 95% recall?"* Those are real questions, and this is the answer to all three.

## Intervals

Sort by start, then sweep:

```python
intervals.sort()
merged = []
for start, end in intervals:
    if merged and start <= merged[-1][1]:
        merged[-1][1] = max(merged[-1][1], end)
    else:
        merged.append([start, end])
```

In ML: merging attention spans, combining overlapping retrieved chunks, and — the one that actually comes up — packing variable-length sequences into fixed-length training batches.

## Graphs

BFS for shortest path on an unweighted graph, DFS for reachability and cycles, topological sort for dependency ordering.

The ML connection is direct and worth naming: **a computation graph is a DAG, and backpropagation is a reverse topological traversal of it.** If an interviewer asks for a topological sort, saying that out loud costs nothing and lands well.

## Dynamic programming

The two that appear in ML contexts:

- **Edit distance** — evaluation metrics, fuzzy matching, diffing model outputs.
- **Viterbi** — the maximum-probability path through a sequence model. Beam search is the approximate version you use when the exact DP is intractable, which is a nice thing to be able to connect.

Do not over-invest here. DP is a smaller share of AI lab loops than of general software interviews.

# Working the Interview

## The sequence that scores

1. **Restate the problem** and confirm the constraints. Input size decides the acceptable complexity, and asking is not a weakness.
2. **Say the brute force out loud** with its complexity. It anchors the conversation and guarantees you have *something*.
3. **State the improvement and its complexity before you write it.** "I can do this in $O(n\log k)$ with a size-$k$ min-heap" — then write it.
4. **Write it.** Clean, named variables, no cleverness.
5. **Trace a small example by hand.** Out loud. This catches most off-by-ones.
6. **Say the edge cases**: empty input, one element, all equal, $k$ larger than $n$, negatives.

## What actually fails candidates

- **Silence.** Thinking without narrating reads as being stuck. Say what you are considering, even when you reject it.
- **Coding before deciding.** Writing while still figuring out the approach produces a mess you then have to defend.
- **Not testing.** Handing over untraced code says you would do the same in production.
- **Refusing a hint.** Hints are given to keep you moving. Taking one gracefully is neutral; resisting one is not.
- **Optimizing prematurely.** A working $O(n^2)$ beats a broken $O(n)$, and the interviewer will tell you if they want better.

## On preparation

Blind 75 or LeetCode 75, worked properly: attempt for 20 minutes, then read the solution and *reimplement it from scratch the next day*. Passive reading of solutions builds recognition, not recall, and the interview tests recall.

Track the patterns you get wrong rather than the problems. Ten missed problems that were all sliding-window is one gap, not ten.
