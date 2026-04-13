#include <cstdint>
#include <iostream>
#include <memory>
#include <optional>
#include <set>
#include <utility>
#include <vector>

constexpr size_t BUCKET_CAPACITY = 4;

// ---------------------------------------------------------------------------
// Bucket
// ---------------------------------------------------------------------------

struct Bucket {
    int local_depth{1};
    std::vector<std::pair<int32_t, int32_t>> entries;
};

// ---------------------------------------------------------------------------
// ExtendibleHashIndex
// ---------------------------------------------------------------------------

class ExtendibleHashIndex {
public:
    ExtendibleHashIndex() : global_depth_(1) {
        // TODO: resize directory_ to 2, create two distinct Bucket shared_ptrs
        //       each with local_depth = 1
    }

    void Insert(int32_t key, int32_t value) {
        // TODO:
        // 1. Compute idx = Index(key)
        // 2. If bucket has space, insert and return
        // 3. If bucket full:
        //    a. If local_depth == global_depth, double the directory
        //    b. Increment local_depth; create new_bucket with same depth
        //    c. Redistribute entries between old and new bucket
        //    d. Update directory pointers for the new bucket
        //    e. Retry: call Insert(key, value) again
    }

    std::optional<int32_t> Lookup(int32_t key) const {
        // TODO: find bucket, linear-scan for key
        return std::nullopt;
    }

    int    GlobalDepth() const { return global_depth_; }

    size_t NumBuckets() const {
        // TODO: count distinct bucket pointers (use std::set<Bucket*>)
        return 0;
    }

private:
    int Index(int32_t key) const {
        // TODO: return key & ((1 << global_depth_) - 1)
        return 0;
    }

    void DoubleDirectory() {
        // TODO: resize to 2x, copy each pointer to the mirrored slot, increment global_depth_
    }

    int                                  global_depth_;
    std::vector<std::shared_ptr<Bucket>> directory_;
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    ExtendibleHashIndex idx;

    for (int32_t k = 1; k <= 10; ++k) idx.Insert(k, k);
    std::cout << "Inserted 10 entries\n";
    std::cout << "Global depth after inserts: " << idx.GlobalDepth() << "\n";
    std::cout << "Num distinct buckets: "       << idx.NumBuckets()  << "\n";

    for (int32_t k = 1; k <= 10; ++k) {
        auto res = idx.Lookup(k);
        if (res) std::cout << "Lookup(" << k << "): found " << *res << "\n";
        else     std::cout << "Lookup(" << k << "): not found\n";
    }
    std::cout << "Lookup(11): " << (idx.Lookup(11) ? "found" : "not found") << "\n";

    return 0;
}
