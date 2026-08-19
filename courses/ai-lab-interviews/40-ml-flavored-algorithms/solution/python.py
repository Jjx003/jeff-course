"""
Five general-coding problems wearing ML costumes.

Each one is a standard pattern applied to something you would actually build in
a lab. Every solution is checked against a brute-force reference on randomized
inputs, which is the habit worth taking into the interview.

Standard library only. Graded output goes to stdout with seed 0.
"""

import heapq
import random
import sys
from collections import Counter, deque

SEED = 0
TRIALS = 300


# ── 1. top-k logits without sorting the vocabulary ──────────────────────


def top_k_indices(logits, k):
    """Indices of the k largest values, largest first. O(n log k), O(k) space.

    This is top-k sampling. A size-k MIN-heap, because you need cheap access
    to the smallest of your current best k in order to evict it.
    """
    if k <= 0:
        return []
    # Store the index negated so that among equal values the LARGEST index is
    # at the root and gets evicted first. Storing it positive evicts the
    # smallest index, which contradicts the documented "ties break by
    # ascending index" rule on every input where a tie straddles k.
    heap = []  # (value, -index)
    for i, value in enumerate(logits):
        if len(heap) < k:
            heapq.heappush(heap, (value, -i))
        elif value > heap[0][0]:
            heapq.heapreplace(heap, (value, -i))
    return [-j for _, j in sorted(heap, key=lambda p: (-p[0], -p[1]))]


def top_k_reference(logits, k):
    order = sorted(range(len(logits)), key=lambda i: (-logits[i], i))
    return order[:k]


# ── 2. merging overlapping spans ────────────────────────────────────────


def merge_spans(spans):
    """Merge overlapping [start, end) token spans. Sort, then sweep.

    Retrieval returns overlapping chunks; attention analyses return
    overlapping spans. Both want the union.
    """
    if not spans:
        return []
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [tuple(s) for s in merged]


def covered_positions(spans):
    """Brute-force reference: the set of covered positions."""
    covered = set()
    for start, end in spans:
        covered.update(range(start, end))
    return covered


# ── 3. packing sequences under a token budget ───────────────────────────


def pack_sequences(lengths, budget):
    """Greedy first-fit-decreasing packing into bins of size `budget`.

    Returns a list of bins, each a list of indices into `lengths`. This is how
    variable-length examples are packed into fixed-length training sequences.
    """
    order = sorted(range(len(lengths)), key=lambda i: -lengths[i])
    bins = []
    remaining = []
    for i in order:
        length = lengths[i]
        if length > budget:
            # A single example longer than the budget gets its own bin; the
            # real system would truncate or split it.
            bins.append([i])
            remaining.append(0)
            continue
        placed = False
        for b, space in enumerate(remaining):
            if space >= length:
                bins[b].append(i)
                remaining[b] -= length
                placed = True
                break
        if not placed:
            bins.append([i])
            remaining.append(budget - length)
    return bins


# ── 4. largest batch that fits: binary search on the answer ─────────────


def largest_feasible(check, lo, hi):
    """Largest x in [lo, hi] with check(x) true, assuming check is monotone.

    'What batch size fits in memory' and 'how many GPUs do I need' are both
    this: the check is expensive, monotone, and you want O(log R) of them.
    """
    if not check(lo):
        return lo - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if check(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# ── 5. rolling token statistics over a window ───────────────────────────


def rolling_distinct(tokens, window):
    """Number of distinct tokens in each window of size `window`.

    Sliding window with a counter. Every token enters and leaves exactly once,
    so it is O(n) despite the two loops.
    """
    if window <= 0 or window > len(tokens):
        return []
    counts = Counter()
    out = []
    queue = deque()
    for token in tokens:
        queue.append(token)
        counts[token] += 1
        if len(queue) > window:
            old = queue.popleft()
            counts[old] -= 1
            if counts[old] == 0:
                del counts[old]
        if len(queue) == window:
            out.append(len(counts))
    return out


def rolling_distinct_reference(tokens, window):
    if window <= 0 or window > len(tokens):
        return []
    return [len(set(tokens[i:i + window])) for i in range(len(tokens) - window + 1)]


# ── Report ──────────────────────────────────────────────────────────────


def main():
    rng = random.Random(SEED)

    # Every printed boolean lands here, so a failure in any section reaches
    # the final verdict. A single reused ok flag silently dropped four of
    # the five fuzz suites.
    checks: list[bool] = []

    def check(label: str, passed: bool) -> bool:
        checks.append(bool(passed))
        print(f"{label}: {passed}")
        return bool(passed)

    print("=== General coding, ML flavored ===")
    print(f"randomized trials per problem: {TRIALS}")

    print()
    print("--- 1. top-k logits (top-k sampling) ---")
    logits = [3.1, -0.5, 9.9, 2.2, 9.9, 0.0, -7.3, 5.5]
    print(f"logits: {logits}")
    print(f"top 3 indices: {top_k_indices(logits, 3)}")
    # 9.9 appears at index 2 and 4; the rule keeps the lower index, and this
    # input exercises the eviction path that the rule actually governs.
    check("ties keep the lower index", top_k_indices([1.0, 9.9, 9.9], 2) == [1, 2])
    check("k = 0 returns empty", top_k_indices(logits, 0) == [])
    check("k > n returns all, ordered", top_k_indices(logits, 99) == top_k_reference(logits, 99))

    ok = True
    for _ in range(TRIALS):
        n = rng.randint(1, 40)
        vals = [round(rng.gauss(0, 5), 3) for _ in range(n)]
        k = rng.randint(1, n)
        ok = ok and top_k_indices(vals, k) == top_k_reference(vals, k)
    # Ties are what the fuzzer above almost never generates, so draw from a
    # small integer range where they are common.
    for _ in range(TRIALS):
        n = rng.randint(1, 12)
        vals = [float(rng.randint(0, 3)) for _ in range(n)]
        k = rng.randint(1, n)
        ok = ok and top_k_indices(vals, k) == top_k_reference(vals, k)
    check(f"matches a full sort on {2 * TRIALS} random inputs, ties included", ok)
    print("(O(n log k) time and O(k) space, versus O(n log n) and O(n) - which")
    print(" is what makes it usable on a 128k vocabulary every decode step)")

    print()
    print("--- 2. merging overlapping spans ---")
    spans = [(5, 9), (0, 3), (2, 6), (12, 14)]
    print(f"spans: {spans}")
    print(f"merged: {merge_spans(spans)}")
    check("empty input", merge_spans([]) == [])
    check("touching spans merge", merge_spans([(0, 5), (5, 9)]) == [(0, 9)])
    check("nested span absorbed", merge_spans([(0, 10), (3, 5)]) == [(0, 10)])

    ok = True
    for _ in range(TRIALS):
        raw = []
        for _ in range(rng.randint(0, 12)):
            start = rng.randint(0, 30)
            raw.append((start, start + rng.randint(1, 8)))
        merged = merge_spans(raw)
        disjoint = all(a[1] < b[0] for a, b in zip(merged, merged[1:]))
        ok = ok and covered_positions(merged) == covered_positions(raw) and disjoint
    check(f"coverage preserved and output disjoint on {TRIALS} random inputs", ok)

    print()
    print("--- 3. packing sequences into a token budget ---")
    lengths = [512, 128, 900, 64, 400, 256, 100]
    budget = 1024
    bins = pack_sequences(lengths, budget)
    used = [sum(lengths[i] for i in b) for b in bins]
    print(f"lengths: {lengths}   budget: {budget}")
    print(f"bins: {bins}")
    print(f"tokens used per bin: {used}")
    check("no bin exceeds the budget", all(u <= budget for u in used))
    check(
        "every sequence placed exactly once",
        sorted(i for b in bins for i in b) == list(range(len(lengths)))
    )
    total = sum(lengths)
    print(f"padding waste: {100 * (len(bins) * budget - total) / (len(bins) * budget):.1f}%")
    print(f"one sequence per bin would waste: {100 * (len(lengths) * budget - total) / (len(lengths) * budget):.1f}%")

    ok = True
    for _ in range(TRIALS):
        lens = [rng.randint(1, 500) for _ in range(rng.randint(1, 20))]
        cap = rng.choice([256, 512, 1024])
        packed = pack_sequences(lens, cap)
        # The escape is only for an item that cannot fit in any bin, not for
        # every single-item bin -- otherwise a packer that never packs passes.
        fits = all(
            sum(lens[i] for i in b) <= cap or (len(b) == 1 and lens[b[0]] > cap)
            for b in packed
        )
        complete = sorted(i for b in packed for i in b) == list(range(len(lens)))
        ok = ok and fits and complete
    check(f"valid packing on {TRIALS} random inputs", ok)

    print()
    print("--- 4. binary search on the answer ---")
    # "How many sequences fit?" Memory grows with batch size; the check is
    # monotone, which is the only property binary search needs.
    def fits(batch):
        return 140 + batch * 1.3 <= 640

    best = largest_feasible(fits, 1, 10000)
    print("weights 140 GB, 1.3 GB of KV cache per sequence, 640 GB available")
    print(f"largest batch that fits: {best}")
    check("it fits and one more does not", fits(best) and not fits(best + 1))

    ok = True
    for _ in range(TRIALS):
        threshold = rng.randint(1, 500)
        found = largest_feasible(lambda x: x <= threshold, 1, 1000)
        ok = ok and found == threshold
    check(f"finds the exact boundary on {TRIALS} random thresholds", ok)
    print("(the check is expensive and monotone, so O(log R) calls beats a scan)")

    print()
    print("--- 5. rolling distinct tokens ---")
    tokens = [1, 2, 2, 3, 1, 1, 4, 5, 5, 5]
    print(f"tokens: {tokens}")
    print(f"distinct per window of 4: {rolling_distinct(tokens, 4)}")
    check("window longer than input returns empty", rolling_distinct(tokens, 99) == [])

    ok = True
    for _ in range(TRIALS):
        stream = [rng.randint(0, 6) for _ in range(rng.randint(1, 30))]
        w = rng.randint(1, len(stream))
        ok = ok and rolling_distinct(stream, w) == rolling_distinct_reference(stream, w)
    check(f"matches the O(nw) reference on {TRIALS} random inputs", ok)
    print("(every token enters and leaves once, so it is O(n) despite two loops)")

    print()
    print(f"checks run: {len(checks)}   failed: {sum(1 for c in checks if not c)}")
    print(f"ALL CHECKS PASS: {all(checks)}")


if __name__ == "__main__":
    main()
