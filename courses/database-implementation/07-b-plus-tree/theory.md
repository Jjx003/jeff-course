# Theory: B+ Tree Index

## Why B+ Trees?

Disk access is expensive: a 4 KB page read costs ~100 µs on an NVMe SSD and ~10 ms on a spinning disk. Searching an unindexed table of $N$ rows requires $O(N/\text{rows\_per\_page})$ disk reads. For $N = 10^8$ rows and 100 rows/page, that is 1 million reads — 100 seconds on an HDD.

A B+ tree keeps the height small. A balanced B+ tree of order $d$ stores up to $2d$ keys per node. With a 4 KB page holding ~200 keys, height 3 serves $200^3 \approx 8 \times 10^6$ keys with at most **3 disk reads** from root to leaf. Height 4 handles 1.6 billion keys in 4 reads.

---

## B vs. B+ Tree

**B tree**: stores key-value pairs in **both** internal and leaf nodes.
- Advantage: sometimes find the value without reaching a leaf.
- Disadvantage: internal nodes are larger (keys + values), reducing branching factor. Range scans require traversing the tree repeatedly.

**B+ tree**: stores values **only** in leaf nodes; internal nodes store separator keys only.
- Internal nodes can hold more keys → higher branching factor → shorter tree.
- Leaves are linked in a sorted linked list → range scans are a single O(range\_size) leaf traversal after finding the start.

Every RDBMS (PostgreSQL, MySQL InnoDB, SQL Server) uses B+ trees for its primary and secondary indexes. B trees appear in filesystems (HFS+, ext4 htree).

---

## Invariants

For a B+ tree of order $d$ (max $2d$ keys per node):

| Node type | Min keys | Max keys | Min children | Max children |
|-----------|----------|----------|--------------|--------------|
| Leaf (non-root) | $d$ | $2d$ | — | — |
| Internal (non-root) | $d$ | $2d$ | $d+1$ | $2d+1$ |
| Root | 1 | $2d$ | 2 | $2d+1$ |

For `ORDER = 4` as used in this module, max keys per node = `ORDER - 1 = 3`, and overflow triggers at `ORDER = 4` keys.

---

## Leaf Split

When a leaf has `ORDER` keys after insert:

$$[\underbrace{k_0 \dots k_{\lfloor m/2 \rfloor - 1}}_{\text{left}}\ |\ \underbrace{k_{\lfloor m/2 \rfloor} \dots k_{m-1}}_{\text{right}}]$$

The first key of the right leaf, $k_{\lfloor m/2 \rfloor}$, is **copied** up to the parent as a separator. The key remains in the right leaf (so range scans work correctly).

---

## Internal Node Split

When an internal node has `ORDER` children after inserting a child pointer:

$$[\underbrace{k_0 \dots k_{m/2-1}}_{\text{left}}\ |\ \underbrace{k_{m/2}}_{\text{promoted}}\ |\ \underbrace{k_{m/2+1} \dots k_{m-1}}_{\text{right}}]$$

The middle key $k_{m/2}$ is **moved** (not copied) to the parent. The left node gets the first half of children, the right node gets the second half. This is the critical difference from leaf splits.

---

## Search

Traverse from root to leaf following separator keys:

```
At internal node with keys [k1, k2, ..., km]:
  if query < k1:   go to children[0]
  if k1 <= query < k2: go to children[1]
  ...
  if query >= km:  go to children[m]
```

At the leaf, scan linearly for the exact key. Linear scan is fast because leaf data is already in cache after the page load.
