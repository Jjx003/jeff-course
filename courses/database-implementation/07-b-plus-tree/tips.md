# Tips & Notes

## Tracking the root type

The root can be either a leaf (empty tree or single-leaf tree) or an internal node. Use a flag:

```cpp
void* root_{nullptr};
bool  root_is_leaf_{true};
```

When inserting into an empty tree, allocate a `LeafNode` and set `root_ = leaf; root_is_leaf_ = true`.

## Returning split info up the call stack

The recursive insert needs to propagate split information upward. A clean approach:

```cpp
struct SplitResult {
    int32_t promoted_key;
    void*   new_right_node;
    bool    new_right_is_leaf;
};

// Returns nullopt if no split, or SplitResult if a split occurred.
std::optional<SplitResult> InsertLeaf(LeafNode* leaf, int32_t key, int32_t val);
std::optional<SplitResult> InsertInternal(InternalNode* node, bool children_are_leaves,
                                           int32_t key, int32_t val);
```

## Sorted insertion into a leaf

```cpp
auto pos = std::lower_bound(leaf->keys.begin(), leaf->keys.end(), key);
size_t idx = pos - leaf->keys.begin();
leaf->keys.insert(pos, key);
leaf->values.insert(leaf->values.begin() + idx, val);
```

## Leaf split

```cpp
// After inserting, leaf has ORDER keys — split
LeafNode* right = new LeafNode();
size_t mid = ORDER / 2;  // = 2 for ORDER=4
right->keys   = {leaf->keys.begin()   + mid, leaf->keys.end()};
right->values = {leaf->values.begin() + mid, leaf->values.end()};
leaf->keys.erase(leaf->keys.begin() + mid, leaf->keys.end());
leaf->values.erase(leaf->values.begin() + mid, leaf->values.end());
right->next = leaf->next;
leaf->next  = right;
int32_t promoted = right->keys[0];  // copy up
```

## Internal node split

```cpp
// internal->keys has ORDER-1 keys, ORDER children → overflow
size_t mid = (ORDER - 1) / 2;  // = 1 for ORDER=4
int32_t promoted = internal->keys[mid];
InternalNode* right = new InternalNode();
right->keys     = {internal->keys.begin() + mid + 1, internal->keys.end()};
right->children = {internal->children.begin() + mid + 1, internal->children.end()};
right->is_leaf_children = internal->is_leaf_children;
internal->keys.erase(internal->keys.begin() + mid, internal->keys.end());
internal->children.erase(internal->children.begin() + mid + 1, internal->children.end());
```

## New root on root split

```cpp
InternalNode* new_root = new InternalNode();
new_root->keys = {promoted_key};
new_root->children = {old_root, new_right};
new_root->is_leaf_children = false;  // children are internal nodes now
root_ = new_root;
root_is_leaf_ = false;
```

## Destructor: free all nodes

Use a recursive post-order traversal:

```cpp
void FreeNode(void* node, bool is_leaf) {
    if (is_leaf) { delete static_cast<LeafNode*>(node); return; }
    auto* in = static_cast<InternalNode*>(node);
    for (void* child : in->children) FreeNode(child, in->is_leaf_children);
    delete in;
}
```
