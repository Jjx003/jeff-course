# General Coding, ML Flavored

Two things are true at once about the general coding interview at an AI lab:

1. It is ordinary LeetCode, and grinding it is a real cost with a real return.
2. It is not what distinguishes candidates — everyone who gets an offer passes it.

The efficient strategy follows from that. You need to be **solidly competent, not exceptional**. Blind 75 or LeetCode 75 gets you there. Two hundred problems is an excellent use of time; a thousand is not, and the marginal hour past competence is better spent on the ML coding interview, which is where the variance actually is.

There is a second reason to care, and it is the one people underweight: **these primitives appear inside ML coding interviews.** Being slow at a heap or a two-pointer scan does not just cost you the general coding round — it eats the clock in the round that matters.

## The distribution of what is actually asked

| Pattern | Frequency | Where it shows up in ML |
|---|---|---|
| Hash maps and sets | very high | vocabulary building, dedup, token counting |
| Two pointers, sliding window | high | context windows, sequence chunking, streaming |
| Heaps / top-k | high | **top-k sampling**, beam search, nearest neighbours |
| Sorting and custom comparators | high | batching by length, ranking outputs |
| Binary search | medium | on the answer, for capacity and threshold problems |
| Intervals | medium | attention spans, sequence packing, span merging |
| Graphs (BFS/DFS/topo sort) | medium | computation graphs, dependency ordering |
| Dynamic programming | medium | edit distance, viterbi, beam pruning |
| Tries | low | tokenizer lookup, prefix caching |
| Linked lists | low | mostly absent at ML labs |

The bolded one is worth noting: **top-k with a heap is the single highest-return general-coding pattern for this domain**, because it is literally the implementation of top-k sampling.

## What "ML flavored" looks like

The same problem, wearing a costume:

- *"Merge overlapping token spans"* — interval merging.
- *"Find the k most likely next tokens without sorting the full vocabulary"* — heap, or `torch.topk`.
- *"Given a stream of tokens, maintain a rolling count over the last W"* — sliding window with a deque.
- *"Given per-sequence lengths, pack them into batches under a token budget"* — greedy bin packing.
- *"Deduplicate documents by shingle overlap"* — hash sets, and then MinHash if they push.
- *"Given a dependency graph of modules, produce a valid execution order"* — topological sort.

The costume does not change the algorithm. Recognizing that quickly, and saying so, is most of the interview.
