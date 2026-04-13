# Tips & Notes

## Initial state

```cpp
ExtendibleHashIndex() : global_depth_(1) {
    directory_.resize(2);
    directory_[0] = std::make_shared<Bucket>();
    directory_[0]->local_depth = 1;
    directory_[1] = std::make_shared<Bucket>();
    directory_[1]->local_depth = 1;
}
```

Two directory entries, two distinct buckets, both local_depth = 1.

## Computing the directory index

```cpp
int Index(int32_t key) const {
    return key & ((1 << global_depth_) - 1);
}
```

## Doubling the directory

```cpp
void DoubleDirectory() {
    size_t old_size = directory_.size();
    directory_.resize(old_size * 2);
    for (size_t i = 0; i < old_size; ++i)
        directory_[old_size + i] = directory_[i];  // duplicate pointers
    ++global_depth_;
}
```

## Updating directory pointers after split

After creating `new_bucket` with `local_depth = new_ld`:

```cpp
int mask = 1 << (new_ld - 1);
int new_pattern = idx & ((1 << new_ld) - 1);  // low new_ld bits of the split index
for (size_t j = 0; j < directory_.size(); ++j) {
    if (directory_[j] == old_bucket) {
        if ((static_cast<int>(j) & ((1 << new_ld) - 1)) == new_pattern) {
            directory_[j] = new_bucket;
        }
    }
}
```

Here `new_pattern` is the specific bit pattern that should map to the new bucket.

## Redistribution

```cpp
auto old_entries = std::move(old_bucket->entries);
old_bucket->entries.clear();
for (auto& [k, v] : old_entries) {
    int new_idx = k & ((1 << new_ld) - 1);
    if (directory_[new_idx] == new_bucket)
        new_bucket->entries.push_back({k, v});
    else
        old_bucket->entries.push_back({k, v});
}
```

## Counting distinct buckets

Use a `std::set<Bucket*>` to count unique raw pointers:

```cpp
size_t NumBuckets() const {
    std::set<Bucket*> seen;
    for (auto& b : directory_) seen.insert(b.get());
    return seen.size();
}
```

## Insert with retry

After a split, call `Insert` again rather than inlining the retry logic. The recursion depth is bounded by the number of splits, which is bounded by the number of entries — so no infinite loop.

```cpp
void Insert(int32_t key, int32_t value) {
    // ... split logic ...
    Insert(key, value);  // retry after split
}
```
