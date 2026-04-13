#include <algorithm>
#include <cstdint>
#include <iostream>
#include <optional>
#include <vector>

constexpr int ORDER = 4;  // max children per internal node; max keys per leaf = ORDER-1

// ---------------------------------------------------------------------------
// Node types
// ---------------------------------------------------------------------------

struct LeafNode {
    std::vector<int32_t> keys;
    std::vector<int32_t> values;
    LeafNode* next{nullptr};
};

struct InternalNode {
    std::vector<int32_t> keys;       // separator keys
    std::vector<void*>   children;
    bool                 is_leaf_children{true};
};

// ---------------------------------------------------------------------------
// BPlusTree
// ---------------------------------------------------------------------------

class BPlusTree {
public:
    BPlusTree() {
        root_ = new LeafNode();
        root_is_leaf_ = true;
    }

    ~BPlusTree() { FreeNode(root_, root_is_leaf_); }

    void Insert(int32_t key, int32_t value) {
        if (root_is_leaf_) {
            auto result = InsertLeaf(static_cast<LeafNode*>(root_), key, value);
            if (result) {
                // Root leaf split — create new root
                auto* new_root = new InternalNode();
                new_root->keys = {result->promoted_key};
                new_root->children = {root_, result->new_right_node};
                new_root->is_leaf_children = true;
                root_ = new_root;
                root_is_leaf_ = false;
            }
        } else {
            auto result = InsertInternal(static_cast<InternalNode*>(root_), key, value);
            if (result) {
                auto* new_root = new InternalNode();
                new_root->keys = {result->promoted_key};
                new_root->children = {root_, result->new_right_node};
                new_root->is_leaf_children = false;
                root_ = new_root;
                root_is_leaf_ = false;
            }
        }
    }

    std::optional<int32_t> Search(int32_t key) const {
        LeafNode* leaf = FindLeaf(key);
        for (size_t i = 0; i < leaf->keys.size(); ++i) {
            if (leaf->keys[i] == key) return leaf->values[i];
        }
        return std::nullopt;
    }

private:
    struct SplitResult {
        int32_t promoted_key;
        void*   new_right_node;
    };

    // Find the leaf where key belongs
    LeafNode* FindLeaf(int32_t key) const {
        if (root_is_leaf_) return static_cast<LeafNode*>(root_);
        void* cur = root_;
        bool  cur_is_leaf = false;
        while (!cur_is_leaf) {
            auto* node = static_cast<InternalNode*>(cur);
            size_t i = 0;
            while (i < node->keys.size() && key >= node->keys[i]) ++i;
            cur_is_leaf = node->is_leaf_children;
            cur = node->children[i];
        }
        return static_cast<LeafNode*>(cur);
    }

    std::optional<SplitResult> InsertLeaf(LeafNode* leaf, int32_t key, int32_t val) {
        auto pos = std::lower_bound(leaf->keys.begin(), leaf->keys.end(), key);
        size_t idx = static_cast<size_t>(pos - leaf->keys.begin());
        leaf->keys.insert(pos, key);
        leaf->values.insert(leaf->values.begin() + static_cast<ptrdiff_t>(idx), val);

        if (static_cast<int>(leaf->keys.size()) < ORDER) return std::nullopt;

        // Split
        size_t mid = ORDER / 2;
        auto* right = new LeafNode();
        right->keys   = {leaf->keys.begin()   + static_cast<ptrdiff_t>(mid), leaf->keys.end()};
        right->values = {leaf->values.begin() + static_cast<ptrdiff_t>(mid), leaf->values.end()};
        leaf->keys.erase(leaf->keys.begin()   + static_cast<ptrdiff_t>(mid), leaf->keys.end());
        leaf->values.erase(leaf->values.begin()+ static_cast<ptrdiff_t>(mid), leaf->values.end());
        right->next = leaf->next;
        leaf->next  = right;
        return SplitResult{right->keys[0], right};
    }

    std::optional<SplitResult> InsertInternal(InternalNode* node, int32_t key, int32_t val) {
        // Find child to descend into
        size_t i = 0;
        while (i < node->keys.size() && key >= node->keys[i]) ++i;

        std::optional<SplitResult> child_split;
        if (node->is_leaf_children) {
            child_split = InsertLeaf(static_cast<LeafNode*>(node->children[i]), key, val);
        } else {
            child_split = InsertInternal(static_cast<InternalNode*>(node->children[i]), key, val);
        }

        if (!child_split) return std::nullopt;

        // Insert promoted key and new right child into this node
        auto kpos = node->keys.begin() + static_cast<ptrdiff_t>(i);
        node->keys.insert(kpos, child_split->promoted_key);
        node->children.insert(node->children.begin() + static_cast<ptrdiff_t>(i) + 1,
                              child_split->new_right_node);

        if (static_cast<int>(node->children.size()) <= ORDER) return std::nullopt;

        // Internal split
        size_t mid = (ORDER - 1) / 2;
        int32_t promoted = node->keys[mid];
        auto* right = new InternalNode();
        right->keys     = {node->keys.begin() + static_cast<ptrdiff_t>(mid) + 1, node->keys.end()};
        right->children = {node->children.begin() + static_cast<ptrdiff_t>(mid) + 1, node->children.end()};
        right->is_leaf_children = node->is_leaf_children;
        node->keys.erase(node->keys.begin() + static_cast<ptrdiff_t>(mid), node->keys.end());
        node->children.erase(node->children.begin() + static_cast<ptrdiff_t>(mid) + 1, node->children.end());
        return SplitResult{promoted, right};
    }

    void FreeNode(void* node, bool is_leaf) {
        if (!node) return;
        if (is_leaf) {
            delete static_cast<LeafNode*>(node);
            return;
        }
        auto* in = static_cast<InternalNode*>(node);
        for (void* child : in->children) FreeNode(child, in->is_leaf_children);
        delete in;
    }

    void*  root_{nullptr};
    bool   root_is_leaf_{true};
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
    auto res = tree.Search(11);
    std::cout << "Search(11): " << (res ? "found" : "not found") << "\n";

    return 0;
}
