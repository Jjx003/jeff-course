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
        directory_.resize(2);
        directory_[0] = std::make_shared<Bucket>();
        directory_[0]->local_depth = 1;
        directory_[1] = std::make_shared<Bucket>();
        directory_[1]->local_depth = 1;
    }

    void Insert(int32_t key, int32_t value) {
        int idx = Index(key);
        auto bucket = directory_[static_cast<size_t>(idx)];

        if (bucket->entries.size() < BUCKET_CAPACITY) {
            bucket->entries.push_back({key, value});
            return;
        }

        // Bucket full — split
        if (bucket->local_depth == global_depth_) {
            DoubleDirectory();
            idx = Index(key);
            bucket = directory_[static_cast<size_t>(idx)];
        }

        int new_ld = bucket->local_depth + 1;
        bucket->local_depth = new_ld;
        auto new_bucket = std::make_shared<Bucket>();
        new_bucket->local_depth = new_ld;

        // Which pattern goes to new bucket? The bit at position (new_ld - 1)
        // The "new" bucket gets the entries where that bit is set (or not),
        // depending on which pattern the original index has.
        int mask_bits = (1 << new_ld) - 1;
        int old_pattern = idx & mask_bits;
        // Flip the top bit to get new pattern
        int new_pattern = old_pattern ^ (1 << (new_ld - 1));

        // Update directory pointers
        for (size_t j = 0; j < directory_.size(); ++j) {
            if (directory_[j] == bucket) {
                if ((static_cast<int>(j) & mask_bits) == new_pattern) {
                    directory_[j] = new_bucket;
                }
            }
        }

        // Redistribute
        auto old_entries = std::move(bucket->entries);
        bucket->entries.clear();
        for (auto& [k, v] : old_entries) {
            int new_idx = k & mask_bits;
            if ((new_idx & mask_bits) == new_pattern)
                new_bucket->entries.push_back({k, v});
            else
                bucket->entries.push_back({k, v});
        }

        // Retry insert
        Insert(key, value);
    }

    std::optional<int32_t> Lookup(int32_t key) const {
        auto bucket = directory_[static_cast<size_t>(Index(key))];
        for (auto& [k, v] : bucket->entries) {
            if (k == key) return v;
        }
        return std::nullopt;
    }

    int GlobalDepth() const { return global_depth_; }

    size_t NumBuckets() const {
        std::set<Bucket*> seen;
        for (auto& b : directory_) seen.insert(b.get());
        return seen.size();
    }

private:
    int Index(int32_t key) const {
        return key & ((1 << global_depth_) - 1);
    }

    void DoubleDirectory() {
        size_t old_size = directory_.size();
        directory_.resize(old_size * 2);
        for (size_t i = 0; i < old_size; ++i)
            directory_[old_size + i] = directory_[i];
        ++global_depth_;
    }

    int                                       global_depth_;
    std::vector<std::shared_ptr<Bucket>>      directory_;
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
    auto res = idx.Lookup(11);
    std::cout << "Lookup(11): " << (res ? "found" : "not found") << "\n";

    return 0;
}
