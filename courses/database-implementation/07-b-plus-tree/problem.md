# B+ Tree Index

## Your Task

Implement `BPlusTree<int32_t, int32_t>` with insert and point search.

### Parameters

```cpp
constexpr int ORDER = 4;  // internal nodes: up to ORDER-1 keys, ORDER children
                           // leaf nodes:     up to ORDER-1 key-value pairs
```

### Node types

```cpp
struct LeafNode {
    std::vector<int32_t> keys;
    std::vector<int32_t> values;
    LeafNode* next{nullptr};   // linked list for range scans
};

struct InternalNode {
    std::vector<int32_t>     keys;       // separator keys (size = children.size()-1)
    std::vector<void*>       children;   // pointers to InternalNode or LeafNode
    bool                     is_leaf_children{false};
};
```

### API

```cpp
class BPlusTree {
public:
    BPlusTree();
    ~BPlusTree();  // free all nodes

    void Insert(int32_t key, int32_t value);
    std::optional<int32_t> Search(int32_t key);
};
```

### Insert algorithm

1. Find the correct leaf by traversing from root: at each internal node, binary-search the separator keys to choose the child.
2. Insert into the leaf in sorted order.
3. If the leaf now has `ORDER` keys (overflow):
   - Split: left leaf keeps first `ORDER/2` pairs, right leaf keeps the rest.
   - Push the first key of the right leaf up as a separator into the parent.
   - If the parent overflows (has `ORDER` children), split the internal node:
     - Middle key is promoted to the grandparent (not copied — it moves up).
     - Continue up recursively.
4. If the root splits, create a new root.

### Search algorithm

Traverse from root to the correct leaf (same as step 1 of insert), then linear-scan the leaf for the key.

## What to Print

Insert keys 1–10 in the order: `5, 3, 7, 1, 4, 6, 8, 2, 9, 10`.

Then search for each key 1–10:

```
Inserted: 5 3 7 1 4 6 8 2 9 10
Search(1): found 1
Search(2): found 2
Search(3): found 3
Search(4): found 4
Search(5): found 5
Search(6): found 6
Search(7): found 7
Search(8): found 8
Search(9): found 9
Search(10): found 10
Search(11): not found
```

## Constraints

- Compile with `g++ -std=c++20 -Wall -Wextra`.
- Use `ORDER = 4` (leaf capacity 3 keys; splits at 4).
- No use of `std::map` or any balanced BST — implement the tree yourself.
- The tree must correctly free all allocated nodes in the destructor (no leaks).
