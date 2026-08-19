"""
Five general-coding problems wearing ML costumes.

Each one is a standard pattern applied to something you would actually build in
a lab. Every solution is checked against a brute-force reference on randomized
inputs, which is the habit worth taking into the interview.

Standard library only. Graded output goes to stdout with seed 0.

Fill in the five TODO blocks.
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

    TODO 1: keep a size-k MIN-heap of (value, index). Push until it holds k,
    then replace the root whenever a larger value arrives. Return the indices
    sorted by descending value, breaking ties by ascending index.

    A min-heap for the k LARGEST: you need constant-time access to the
    smallest of your current best k, because that is the one you evict.
    Use heapq.heapreplace rather than a pop followed by a push - one sift
    instead of two.
    """
    raise NotImplementedError


def top_k_reference(logits, k):
    order = sorted(range(len(logits)), key=lambda i: (-logits[i], i))
    return order[:k]


# ── 2. merging overlapping spans ────────────────────────────────────────


def merge_spans(spans):
    """Merge overlapping [start, end) token spans. Sort, then sweep.

    Retrieval returns overlapping chunks; attention analyses return
    overlapping spans. Both want the union.

    TODO 2: sort by start, then sweep. If the current span starts at or
    before the end of the last merged one, extend that one; otherwise append.
    Return a list of tuples.

    Comparing against merged[-1] alone is sufficient, and worth being able to
    justify: after sorting by start, its end is the maximum end seen so far,
    so anything overlapping an earlier span must overlap it too.
    """
    raise NotImplementedError


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

    TODO 3: first-fit-decreasing. Sort indices by descending length, then for
    each one place it in the first bin with room, or open a new bin. Track
    remaining capacity per bin alongside the bins themselves.

    Bin packing is NP-hard, so this is a heuristic - say that immediately in
    an interview. Descending order because large items are the hard ones to
    place, so you place them while bins are still empty.

    Handle the case of a single example longer than the budget: give it its
    own bin (a real system would truncate or split it).
    """
    raise NotImplementedError


# ── 4. largest batch that fits: binary search on the answer ─────────────


def largest_feasible(check, lo, hi):
    """Largest x in [lo, hi] with check(x) true, assuming check is monotone.

    'What batch size fits in memory' and 'how many GPUs do I need' are both
    this: the check is expensive, monotone, and you want O(log R) of them.

    TODO 4: binary search for the boundary. Maintain the invariant that lo is
    always feasible and everything above hi is infeasible, and shrink the
    bracket until they meet.

    Two traps, and they are the whole exercise:

      - Because lo moves up to a mid that PASSED, the midpoint must round UP,
        not down. With the floor midpoint, mid equals lo once hi == lo + 1;
        if check(mid) passes, lo never moves and you loop forever. That exact
        infinite loop is one of the most common binary-search bugs there is.

      - check(lo) can be false from the start, meaning nothing in [lo, hi]
        is feasible. Detect that up front and return lo - 1.
    """
    raise NotImplementedError


# ── 5. rolling token statistics over a window ───────────────────────────


def rolling_distinct(tokens, window):
    """Number of distinct tokens in each window of size `window`.

    Sliding window with a counter. Every token enters and leaves exactly once,
    so it is O(n) despite the two loops.

    TODO 5: slide a deque of the current window alongside a Counter of its
    contents. Append on the right, evict on the left once the window is full,
    and record len(counts) at each full window.

    DELETE zero-count keys when evicting, or len(counts) keeps counting
    tokens that have already left the window. That bug only shows on inputs
    where a token leaves and never returns - which fuzzing finds and
    hand-picked cases usually do not.

    Return an empty list when the window is larger than the input.
    """
    raise NotImplementedError


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
