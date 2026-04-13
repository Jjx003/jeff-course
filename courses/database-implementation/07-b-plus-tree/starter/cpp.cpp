#include <algorithm>
#include <cstdint>
#include <iostream>
#include <optional>
#include <vector>

constexpr int ORDER = 4;

// ---------------------------------------------------------------------------
// Node types — do not change the struct definitions
// ---------------------------------------------------------------------------

struct LeafNode {
    std::vector<int32_t> keys;
    std::vector<int32_t> values;
    LeafNode* next{nullptr};
};

struct InternalNode {
    std::vector<int32_t> keys;
    std::vector<void*>   children;
    bool                 is_leaf_children{true};
};

// ---------------------------------------------------------------------------
// BPlusTree
// ---------------------------------------------------------------------------

class BPlusTree {
public:
    BPlusTree() {
        // TODO: allocate an empty LeafNode as root_; set root_is_leaf_ = true
    }

    ~BPlusTree() {
        // TODO: recursively free all nodes
    }

    void Insert(int32_t key, int32_t value) {
        // TODO:
        // If root is a leaf, call InsertLeaf on it.
        //   If split → create new InternalNode root with two children.
        // If root is internal, call InsertInternal on it.
        //   If split → create new InternalNode root.
    }

    std::optional<int32_t> Search(int32_t key) const {
        // TODO: find leaf, linear scan for key
        return std::nullopt;
    }

private:
    struct SplitResult {
        int32_t promoted_key;
        void*   new_right_node;
    };

    // Find leaf where key belongs.
    LeafNode* FindLeaf(int32_t key) const {
        // TODO: traverse from root_ following separator keys
        return nullptr;
    }

    // Insert into leaf. Return SplitResult if overflow, nullopt otherwise.
    std::optional<SplitResult> InsertLeaf(LeafNode* leaf, int32_t key, int32_t val) {
        // TODO:
        // 1. Insert (key, val) in sorted position
        // 2. If leaf has ORDER keys: split and return SplitResult
        return std::nullopt;
    }

    // Insert into subtree rooted at internal node. Propagate splits upward.
    std::optional<SplitResult> InsertInternal(InternalNode* node, int32_t key, int32_t val) {
        // TODO:
        // 1. Find correct child index i
        // 2. Recurse into child (leaf or internal)
        // 3. If child split: insert promoted_key and new_right into this node
        // 4. If this node overflows: split and return SplitResult
        return std::nullopt;
    }

    // Recursively free nodes
    void FreeNode(void* node, bool is_leaf) {
        // TODO
    }

    void* root_{nullptr};
    bool  root_is_leaf_{true};
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    BPlusTree tree;

    std::vector<int32_t> insert_order = {5, 3, 7, 1, 4, 6, 8, 2, 9, 10};
    std::cout << "Inserted:";
    for (int32_t k : insert_order) {
        tree.Insert(k, k);
        std::cout << " " << k;
    }
    std::cout << "\n";

    for (int32_t k = 1; k <= 10; ++k) {
        auto res = tree.Search(k);
        if (res) std::cout << "Search(" << k << "): found " << *res << "\n";
        else     std::cout << "Search(" << k << "): not found\n";
    }
    std::cout << "Search(11): " << (tree.Search(11) ? "found" : "not found") << "\n";

    return 0;
}
