# Theory: Disk Manager

## The Storage Hierarchy and I/O Cost

Modern hardware has a storage hierarchy where each level differs by orders of magnitude in latency:

| Level | Latency | Bandwidth |
|-------|---------|-----------|
| L1 cache | 1 ns | — |
| DRAM | 100 ns | 50 GB/s |
| NVMe SSD | 100 µs | 7 GB/s |
| SATA SSD | 500 µs | 550 MB/s |
| HDD | 10 ms | 200 MB/s |

A single random HDD read is 10 million ns — 10 million times slower than an L1 cache hit. This asymmetry is why databases read and write in pages (4–16 KB), not bytes: the cost of initiating a disk I/O is amortised across the entire page.

---

## Page-Aligned I/O

Page `id` lives at byte offset $\text{id} \times \text{PAGE\_SIZE}$ in the file. Because `PAGE_SIZE` is a power of two and the OS block size is also a power of two (typically 4096 bytes), each page aligns exactly to a filesystem block. This enables:

- **Direct I/O** (`O_DIRECT`): bypass the OS page cache and read/write directly to disk buffer. Used by databases that manage their own cache (the buffer pool).
- **`mmap`** as an alternative: map the file into virtual memory and let the OS manage pages. Simpler but gives up control over eviction policy.

---

## `pread` / `pwrite` vs `read` / `write`

`read(fd, buf, n)` reads `n` bytes starting at the **current file offset** and advances it. This is stateful: concurrent reads from multiple threads clobber each other's offset.

`pread(fd, buf, n, offset)` reads `n` bytes at the specified `offset` without modifying the file offset. It is atomic with respect to position — multiple threads can safely call `pread` on the same fd concurrently. This is the correct primitive for a multi-threaded buffer pool where several threads fetch pages simultaneously.

---

## Why Not `std::fstream`?

`fstream` wraps C-style `FILE*` buffered I/O. The internal buffer layer:
1. Adds an extra copy through the stdio buffer.
2. Does not expose `pread`/`pwrite` semantics.
3. Makes it impossible to use `O_DIRECT` or `fsync` reliably.

Production database storage engines (PostgreSQL, RocksDB, LevelDB, WiredTiger) all use POSIX file I/O directly.

---

## `fsync` and Durability

`pwrite` delivers data to the OS page cache, not necessarily to disk. A crash before the OS flushes the cache loses the write. `fsync(fd)` forces all dirty pages for `fd` to durable storage. In a crash-safe database:

- The WAL (Write-Ahead Log) calls `fsync` after each log flush.
- `fsync` on the data file is called during checkpoints.

For this module you do not need `fsync` — durability is not required. But the architecture exists: every `WritePage` queues a page for later `fsync` during a checkpoint.

---

## `ftruncate` for Pre-allocation

`ftruncate(fd, new_size)` extends or truncates a file to exactly `new_size` bytes. On Linux, extending creates a "sparse file" — the new bytes read as zero without consuming disk blocks until written. This is how `AllocatePage` extends the file cheaply: no actual disk write until `WritePage` fills the page.
