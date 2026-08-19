# The Complexity Table

| Structure | Access | Insert | Delete | Search |
|---|---|---|---|---|
| Array | $O(1)$ | $O(n)$ | $O(n)$ | $O(n)$ |
| Hash map | — | $O(1)$ avg | $O(1)$ avg | $O(1)$ avg |
| Heap | $O(1)$ min/max | $O(\log n)$ | $O(\log n)$ | $O(n)$ |
| Balanced BST | — | $O(\log n)$ | $O(\log n)$ | $O(\log n)$ |
| Trie | — | $O(m)$ | $O(m)$ | $O(m)$ |

| Algorithm | Time | Space |
|---|---|---|
| Sort | $O(n\log n)$ | $O(n)$ or $O(\log n)$ |
| Top-k with a heap | $O(n\log k)$ | $O(k)$ |
| Quickselect | $O(n)$ average | $O(1)$ |
| Binary search | $O(\log n)$ | $O(1)$ |
| BFS / DFS | $O(V+E)$ | $O(V)$ |
| Topological sort | $O(V+E)$ | $O(V)$ |

# Python Notes

```python
import heapq
heapq.heappush(h, x); heapq.heappop(h)      # MIN-heap only
heapq.heapreplace(h, x)                      # pop then push, one sift
heapq.nlargest(k, it, key=...)               # when you just want the answer
[-x for x in vals]                           # the max-heap idiom

from collections import defaultdict, Counter, deque
Counter(items).most_common(k)
deque(maxlen=w)                              # sliding window, O(1) at both ends

import bisect
bisect.bisect_left(sorted_list, x)           # first index >= x
sorted(items, key=lambda t: (-t.score, t.id))  # descending then tie-break
```

# Rapid-Fire Answers

**"Find the k largest in a stream."**
> A size-k min-heap. Push until it holds k, then replace the root whenever a larger value arrives. `O(n log k)` time, `O(k)` space. A min-heap for the k *largest*, because you need cheap access to the smallest of your current best in order to evict it.

**"Top-k over a 128k vocabulary, every decoding step."**
> Do not sort the vocabulary. `torch.topk` is a partial selection; if you need the set but not the order, quickselect is `O(n)` on average. This is literally how top-k sampling is implemented.

**"How would you find the largest batch size that fits?"**
> Binary search on the answer. The feasibility check — does this batch fit in memory — is monotone in batch size, so `O(log R)` checks suffice.

**"Why is the sliding-window template linear when it has a nested loop?"**
> Every element is added once and removed at most once, so the inner loop's total work across the whole run is bounded by `n`. Amortized `O(n)`.

**"What is the connection between topological sort and backprop?"**
> A computation graph is a DAG. The forward pass is a topological traversal; backprop is the reverse topological traversal, which is exactly why gradients must be accumulated at nodes with multiple consumers.

# Further Reading

- [NeetCode Blind 75](https://neetcode.io/practice) — the right list, organized by pattern rather than by difficulty.
- [LeetCode 75](https://leetcode.com/studyplan/leetcode-75/) — an equivalent alternative.
- [Python heapq docs](https://docs.python.org/3/library/heapq.html) — worth reading in full once; it is short, and `nlargest` and `heapreplace` save real time.
