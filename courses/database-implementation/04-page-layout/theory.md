# Theory: Page Layout — Slotted Pages

## Why Pages?

The fundamental unit of I/O in a database is the **page** (typically 4–16 KB). Reading or writing anything smaller than a page is wasteful because the OS and disk hardware operate at block granularity anyway. Every table row, index key, and overflow chunk is stored in a page, identified by a `(file_id, page_id)` pair.

---

## Slotted-Page Layout

A slotted page organises variable-length tuples without external fragmentation:

```
┌──────────────────────────────────────────┐  ← offset 0
│  Header: num_slots | free_space_offset   │
├──────────────────────────────────────────┤  ← offset 4
│  Slot 0: (offset, length)               │
│  Slot 1: (offset, length)               │
│  ...                                     │  ← slot array grows →
│                 free space               │
│           ← tuples grow ←               │
│  Tuple 1 data                            │
│  Tuple 0 data                            │
└──────────────────────────────────────────┘  ← offset 4096
```

Key properties:
- Slots are fixed-size (4 bytes each), so slot `i` is at `offset 4 + 4*i`.
- Tuple data is packed from the **end of the page** upward, so `free_space_offset` decreases with each insert.
- The two regions grow toward each other; insertion fails when they would collide.

### Why grow from both ends?

Fixed-size slot entries at the front allow O(1) lookup by `slot_id` without scanning. Variable-length tuples at the back avoid wasted space from padding. The meeting-in-the-middle design minimises fragmentation.

---

## Internal vs. External Fragmentation

**Internal fragmentation**: wasted space inside allocated regions (e.g., padding). Slotted pages have none for tuple data — tuples are packed with no gaps.

**External fragmentation**: free space scattered in small unusable chunks. Slotted pages accumulate external fragmentation as tuples are deleted, leaving holes. Reclaiming this space requires **page compaction** (vacuum in PostgreSQL): slide all live tuples to the end and reset `free_space_offset`.

---

## NSM vs. DSM

**NSM (N-ary Storage Model)** — row store. All columns of a row are stored together in one tuple on one page. Good for OLTP (fetch one full row per lookup).

**DSM (Decomposition Storage Model)** — column store. Each column is stored in its own page run. Good for OLAP (scan one column across millions of rows, maximise cache utilisation, enable SIMD compression).

Modern systems (DuckDB, Snowflake) use **PAX** (Partition Attributes Across) — a hybrid: pages are column-oriented internally, but data is partitioned into row-groups to preserve locality.

This module implements NSM, which is what PostgreSQL, MySQL, and SQLite use for their heap files.

---

## Deletion and Tombstones

Setting `length = 0` marks a slot as a tombstone. The slot entry stays in the array so existing slot IDs don't change — this is critical for index correctness. A B+ tree index entry points to `(page_id, slot_id)`; if deletion shifted slot IDs, every index entry on that page would be invalidated. Tombstones let the index safely ignore the slot on the next lookup.

Free space is **not** reclaimed by deletion alone — you still need compaction (or a new insert over the same slot, which requires additional "slot reuse" logic not required here).
