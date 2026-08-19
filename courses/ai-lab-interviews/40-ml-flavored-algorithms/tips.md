# Debugging Guide

**Top-k returns the k smallest.** You used a max-heap, or compared with `<`. For the k largest you keep a min-heap and evict its root.

**Top-k differs from the reference only on ties.** Pick a tie-break rule and apply it in both. The reference here uses `(-value, index)`.

**Span merging leaves overlaps.** You compared against the wrong element, or forgot to sort. Compare against `merged[-1]` only — after sorting by start, that is provably sufficient.

**Packing loses or duplicates an item.** A `continue` that skips the bookkeeping, or a bin appended without a matching remaining-capacity entry. The invariant check catches it.

**Binary search hangs.** The classic. With `mid = (lo + hi) // 2` and the `check(mid) -> lo = mid` branch, `mid` equals `lo` when `hi == lo + 1` and nothing moves. Use `(lo + hi + 1) // 2` for that direction.

**Rolling distinct is too high.** You are not deleting zero-count keys, so the counter still holds tokens that left the window.

# Rapid-Fire Answers

**"Find the k largest values in a stream."**
> Size-k min-heap. Push until it holds k, then replace the root whenever something larger arrives. `O(n log k)` time, `O(k)` space. Min-heap for the k largest, because eviction needs the smallest of the current best.

**"How would you test this?"**
> Fuzz it against a brute-force reference on randomized inputs, plus hand-picked edge cases for what random generation is unlikely to produce. Where there is no unique correct answer — packing, for instance — assert the invariants instead.

**"How do you pack variable-length sequences?"**
> Bin packing, so a greedy heuristic. First-fit-decreasing: sort descending, place each into the first bin with room. Large items are the hard ones, so place them while bins are empty. Within about 22% of optimal in the worst case, and much better in practice.

**"Largest batch size that fits?"**
> Binary search on the answer. The check is monotone in batch size and expensive, so `O(log R)` checks beats a linear scan. Watch the `+1` in the midpoint or you will loop forever.

**"Why is the sliding window O(n) with two loops?"**
> Every element is added once and removed at most once, so the inner loop's total work across the whole run is bounded by `n`. Amortized linear.

# What to Say While You Type

The sequence that scores, on any of these:

> "This is a top-k problem, so a heap. Brute force is sort the whole thing, `O(n log n)` — fine for small inputs. Since I only need k, a size-k min-heap gives `O(n log k)` and `O(k)` space, which matters because this is a 128k vocabulary. Min-heap for the k largest because I need to evict the smallest of my current best. Let me write it, then trace a five-element example, then fuzz it against the sort."

That covers pattern recognition, brute force, improvement with complexity, the counterintuitive detail, and testing — before writing a line.

# Further Reading

- [NeetCode Blind 75](https://neetcode.io/practice) — organized by pattern, which is how to study it.
- [Python heapq docs](https://docs.python.org/3/library/heapq.html) — short, and `nlargest`/`heapreplace` save real interview time.
- [Hypothesis](https://hypothesis.readthedocs.io/) — property-based testing, if you want to do the fuzzing habit properly outside interviews.
