# Theory: Extendible Hash Index

## Hash Indexes vs. B+ Trees

| Property | Hash index | B+ tree |
|----------|-----------|---------|
| Point lookup | O(1) avg | O(log N) |
| Range scan | Not supported | O(log N + k) |
| Ordered iteration | No | Yes |
| Space | Compact | Compact |
| Worst-case lookup | O(N) (all keys same hash) | O(log N) |

Use a hash index when queries are always equality predicates (`WHERE id = ?`) and you never need `ORDER BY` or range scans. Use a B+ tree when you need either.

---

## Extendible Hashing

Static hashing pre-allocates a fixed number of buckets. When a bucket overflows, you either chain overflow pages (poor cache behaviour) or rehash the entire table (expensive). Extendible hashing solves both problems with a two-level structure:

**Directory**: an array of $2^{\text{global\_depth}}$ pointers to buckets.
**Buckets**: the actual storage, shared between multiple directory entries.

The **global depth** $g$ determines how many low-order bits of the hash are used to index the directory. A **local depth** $l \le g$ on each bucket says how many bits distinguish entries in that bucket.

### Why shared pointers?

When $l < g$, multiple directory entries point to the same bucket. For example with $g=2$ and a bucket with $l=1$:
- Directory entry `00` and `10` both point to bucket B.
- Directory entry `01` and `11` both point to bucket C.

This sharing is why doubling the directory is cheap: copy each pointer twice — no data moves.

---

## Bucket Split Algorithm

When bucket $b$ at directory index $i$ overflows:

1. **If $l == g$**: double the directory. Because the directory is indexed by the **low-order** bits of the hash, each old entry is simply duplicated — adding a high bit must not change which bucket an existing index maps to. For $j$ in $[0, 2^{g+1})$, set `dir[j] = old_dir[j & (2^g - 1)]` (equivalently `old_dir[j mod 2^g]`). Then $g \leftarrow g+1$.

2. **Increment local depth**: $b.l \leftarrow b.l + 1$.

3. **Create new bucket** $b'$ with same local depth.

4. **Redistribute**: for each entry $(k, v)$ in $b$, compute the new directory index using $b.l$ bits. If `(hash(k) >> (b.l - 1)) & 1 == 1`, move to $b'$.

5. **Update directory pointers**: all directory entries whose index matches $b'$'s pattern now point to $b'$.

6. **Retry insert** (the key that caused the overflow).

---

## Directory Doubling

Before: directory size $= 2^g$, global depth $= g$.
After:  directory size $= 2^{g+1}$, global depth $= g+1$.

```
Before (g=1): [B0, B1]
After  (g=2): [B0, B1, B0, B1]   (low-order indexing: entry j keeps the
                                  bucket of index j mod 2^old_g)
```

Note: this only copies pointers, not data. The directory itself is small (at most $2^{32}$ entries in theory, but in practice bounded by the number of pages times bits-per-page).

---

## O(1) Lookup

Lookup computes one hash → one array index → one bucket scan. The bucket fits in one or a few cache lines. No pointer chasing (unlike chained hashing). The directory itself may or may not fit in cache depending on global depth, but even a miss there costs one cache line fetch.

---

## Limitations

- **Skewed keys**: if all keys hash to the same prefix, splitting is useless and one bucket remains full. A better hash function (e.g., multiply-shift) reduces this risk.
- **No ordering**: unlike a B+ tree, you cannot iterate keys in order.
- **Directory size**: in the worst case the directory doubles to $2^{32}$ entries — impractical. Real systems cap the global depth or fall back to overflow chains.
