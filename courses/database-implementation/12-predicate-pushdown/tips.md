# Tips & Notes

## unique_ptr tree manipulation

When you push a `FilterNode` below a `JoinNode`, you need to move ownership:

```cpp
// Before: Filter → Join → (A, B)
// After:  Join → (Filter → A, B)

// Detach the join from the filter
auto join = std::move(filter->child);
// Wrap the left child of the join with the filter
auto new_filter = MakeFilter(std::move(join->left), filter->predicate_str, filter->predicate_table);
join->left = std::move(new_filter);
// Return the join (bypassing the filter)
return join;
```

Never copy a `unique_ptr` — always `std::move`.

## Recursive Apply

```cpp
static std::unique_ptr<PlanNode> Apply(std::unique_ptr<PlanNode> root) {
    if (!root) return root;

    // Recurse into children first (bottom-up) or apply rule then recurse (top-down).
    // Top-down is simpler for this rule.

    if (root->type == NodeType::Filter && root->child &&
        root->child->type == NodeType::Join) {
        // Check if predicate references only left or only right child
        auto& join = root->child;
        if (LeftChildTable(join.get()) == root->predicate_table) {
            // Push filter to left
            auto new_left = MakeFilter(std::move(join->left),
                                       root->predicate_str, root->predicate_table);
            join->left = Apply(std::move(new_left));  // recurse on new subtree
            return Apply(std::move(join));             // retry from join
        } else if (RightChildTable(join.get()) == root->predicate_table) {
            // Push filter to right
            auto new_right = MakeFilter(std::move(join->right),
                                        root->predicate_str, root->predicate_table);
            join->right = Apply(std::move(new_right));
            return Apply(std::move(join));
        }
    }

    // Recurse into children
    if (root->child) root->child = Apply(std::move(root->child));
    if (root->left)  root->left  = Apply(std::move(root->left));
    if (root->right) root->right = Apply(std::move(root->right));
    return root;
}
```

## LeftChildTable / RightChildTable helpers

```cpp
static std::string RootTable(const PlanNode* node) {
    switch (node->type) {
        case NodeType::Scan:   return node->table_name;
        case NodeType::Filter: return RootTable(node->child.get());
        case NodeType::Project:return RootTable(node->child.get());
        default:               return "";  // Join — references multiple tables
    }
}
```

## PrintPlan with indent

```cpp
void PrintPlan(const PlanNode* node, int indent) {
    std::string pad(indent * 2, ' ');
    switch (node->type) {
        case NodeType::Scan:
            std::cout << pad << "Scan [" << node->table_name << "]\n"; break;
        case NodeType::Filter:
            std::cout << pad << "Filter [" << node->predicate_str
                      << "] on " << node->predicate_table << "\n";
            PrintPlan(node->child.get(), indent + 1); break;
        case NodeType::Project: {
            std::cout << pad << "Project [";
            for (size_t i=0;i<node->cols.size();++i){ if(i)std::cout<<", "; std::cout<<node->cols[i]; }
            std::cout << "]\n";
            PrintPlan(node->child.get(), indent + 1); break;
        }
        case NodeType::Join:
            std::cout << pad << "Join [" << node->join_condition << "]\n";
            PrintPlan(node->left.get(),  indent + 1);
            PrintPlan(node->right.get(), indent + 1); break;
    }
}
```
