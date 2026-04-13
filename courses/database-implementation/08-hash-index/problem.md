# Extendible Hash Index

## Your Task

Implement `ExtendibleHashIndex<int32_t, int32_t>` using extendible hashing.

### Data structures

```cpp
constexpr size_t BUCKET_CAPACITY = 4;

struct Bucket {
    int local_depth{1};
    std::vector<std::pair<int32_t, int32_t>> entries;  // (key, value)
};

class ExtendibleHashIndex {
public:
    ExtendibleHashIndex();   // global_depth = 1, two empty buckets

    void Insert(int32_t key, int32_t value);
    std::optional<int32_t> Lookup(int32_t key);

    int GlobalDepth() const;
    size_t NumBuckets() const;   // count distinct bucket objects (not dir size)
};
```

### Hash function

Use the low-order `global_depth` bits of the key as the bucket index:

```cpp
int hash(int32_t key) { return key & ((1 << global_depth_) - 1); }
```

### Insert algorithm

1. Compute `hash(key)`. Access `directory_[hash(key)]`.
2. If `entries.size() < BUCKET_CAPACITY`, insert directly.
3. Otherwise (bucket full):
   a. If `local_depth == global_depth`: **double the directory** (copy each pointer twice).
   b. Increment `local_depth` for the bucket.
   c. Create a new bucket with `local_depth` = same new value.
   d. **Redistribute** all entries in the old bucket between old and new using the updated hash bit.
   e. Update all directory pointers that point to the old bucket: entries whose `(index & mask)` matches the new bucket go to the new bucket.
   f. Retry the insert.

### Lookup

Compute `hash(key)`, find the bucket, linear-scan for key.

## What to Print

```
Inserted 10 entries
Global depth after inserts: 2
Num distinct buckets: 3
Lookup(1): found 1
Lookup(2): found 2
Lookup(3): found 3
Lookup(4): found 4
Lookup(5): found 5
Lookup(6): found 6
Lookup(7): found 7
Lookup(8): found 8
Lookup(9): found 9
Lookup(10): found 10
Lookup(11): not found
```

Insert the keys 1–10 in order.

## Constraints

- Compile with `g++ -std=c++20 -Wall -Wextra`.
- `BUCKET_CAPACITY = 4`.
- `directory_` is `std::vector<std::shared_ptr<Bucket>>`.
- No external hash table libraries.
