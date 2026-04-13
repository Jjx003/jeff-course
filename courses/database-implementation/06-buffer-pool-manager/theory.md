# Theory: Buffer Pool Manager

## Architecture

The buffer pool sits between the disk manager and every other component:

```
Query Executor
      │ FetchPage / UnpinPage
      ▼
BufferPoolManager
  ┌─────────────────────────┐
  │  Frame 0: page 7, pin=2 │
  │  Frame 1: page 3, pin=0 │
  │  Frame 2: page 12, pin=1│
  └─────────────────────────┘
      │ ReadPage / WritePage
      ▼
  DiskManager  →  file.db
```

The buffer pool's job: keep hot pages in memory, evict cold pages when the pool is full, ensure dirty pages are written back before their frame is reused.

---

## Pin Count

A **pin count** tracks how many threads or operators are currently using a frame. A frame with `pin_count > 0` cannot be evicted — it would corrupt any ongoing read or write.

Protocol:
1. `FetchPage(id)` → increments `pin_count`. Returns a raw pointer to the frame. The caller **must** call `UnpinPage` when done.
2. `UnpinPage(id, dirty)` → decrements `pin_count`. If `dirty=true`, sets `is_dirty`. When `pin_count` drops to 0, the frame is eviction-eligible.

This is analogous to reference counting, but manual — the caller, not the runtime, decides when it is done with a page. Database engines prefer manual control because a single page can be pinned/unpinned multiple times within a query with predictable scoping.

---

## Dirty Bits

A page is **dirty** if its in-memory content differs from what is on disk. Before evicting a dirty frame, the buffer pool must `WritePage` it to disk. Evicting without flushing is data loss.

The `UnpinPage(id, dirty=true)` call is how a modifying operator signals that it changed the page — the buffer pool records the dirty flag and will flush when evicting.

---

## LRU Eviction

**Least Recently Used (LRU)**: evict the frame that was least recently accessed. Implementation:

- Maintain a doubly-linked list of **eviction-eligible** frames (pin_count == 0).
- On access: move to front (O(1) with `std::list::splice` + an iterator map).
- On evict: take from back.

**LRU-K** (used in real systems like PostgreSQL): track the `K`-th most recent access time. This avoids the "sequential flood" problem where a large table scan thrashes the cache by evicting hot pages. For this exercise, plain LRU (K=1) is sufficient.

---

## Page Table

The **page table** is a hash map from `page_id_t` to `frame_id_t`. It answers the question "is page X currently in memory, and if so which frame?" in O(1).

Not to be confused with the OS virtual memory page table — the database page table is entirely in user space.

---

## NewPage vs. FetchPage

`NewPage` allocates a new page on disk (via `DiskManager::AllocatePage`) and loads it into a frame. The frame starts zeroed and dirty (it has not been written to disk yet, though some implementations skip the initial flush). `FetchPage` loads an **existing** page from disk into a frame.

---

## Why Not Just Use `mmap`?

`mmap` lets the OS manage page eviction. This is simpler but gives up:
1. **Eviction control**: the OS knows nothing about access patterns within the DB. LRU-K dramatically outperforms OS LRU for DB workloads.
2. **Durability control**: `msync` is coarse; the DB cannot fsync individual pages in the right order for crash recovery.
3. **I/O scheduling**: the DB cannot issue async prefetch hints.

SQLite uses `mmap` optionally for read-only access. PostgreSQL 15 added a `mmap` option but disabled it by default. High-performance engines (PostgreSQL, MySQL InnoDB, RocksDB) all implement their own buffer pool.
