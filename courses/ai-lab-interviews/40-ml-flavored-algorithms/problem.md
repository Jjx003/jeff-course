# ML-Flavored Algorithms

Five problems. Each one is a textbook pattern wearing a costume you will recognize from the rest of this course.

They are here for two reasons. First, this is what a general coding round at an AI lab tends to look like — LeetCode with domain dressing. Second, every one of these is something you would genuinely write: `top_k_indices` *is* top-k sampling, and `pack_sequences` *is* what the data loader does.

## What to implement

1. `top_k_indices` — the k largest logits without sorting the vocabulary. Heap.
2. `merge_spans` — union of overlapping token spans. Sort and sweep.
3. `pack_sequences` — pack variable-length examples into fixed-size training sequences. Greedy first-fit-decreasing.
4. `largest_feasible` — largest batch size that fits, given a monotone feasibility check. Binary search on the answer.
5. `rolling_distinct` — distinct tokens in each window. Sliding window with a counter.

## How the script checks you

Every solution is compared against a **brute-force reference on 300 randomized inputs**, plus a handful of hand-chosen edge cases.

That is deliberate, and it is the habit worth taking into the interview. When you finish an implementation and the interviewer asks how you would test it, "I would write the obvious slow version and fuzz them against each other" is a much better answer than a list of cases you thought of. It also finds real bugs — the edge case you did not think of is, by construction, the one you did not test.

## The one to get exactly right

`top_k_indices` uses a **min-heap** to find the **k largest**. That inversion trips people up under pressure, and the reason is worth being able to state: you need constant-time access to the *smallest* of your current best k, because that is the one you evict when something better arrives.
