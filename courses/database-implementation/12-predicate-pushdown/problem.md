# Predicate Pushdown

## Your Task

Implement a logical plan tree and a predicate pushdown rewrite rule.

### Node types

```cpp
enum class NodeType { Scan, Filter, Project, Join };

struct PlanNode {
    NodeType type;
    std::string table_name;       // Scan only
    std::string predicate_str;    // Filter only (e.g. "id > 3")
    std::string predicate_table;  // Filter only — which table the predicate references
    std::vector<std::string> cols;// Project only
    std::string join_condition;   // Join only
    std::unique_ptr<PlanNode> child;       // Filter, Project
    std::unique_ptr<PlanNode> left;        // Join
    std::unique_ptr<PlanNode> right;       // Join
};
```

Provide factory functions:
```cpp
std::unique_ptr<PlanNode> MakeScan(std::string table);
std::unique_ptr<PlanNode> MakeFilter(std::unique_ptr<PlanNode> child,
                                      std::string pred, std::string pred_table);
std::unique_ptr<PlanNode> MakeProject(std::unique_ptr<PlanNode> child,
                                       std::vector<std::string> cols);
std::unique_ptr<PlanNode> MakeJoin(std::unique_ptr<PlanNode> left,
                                    std::unique_ptr<PlanNode> right,
                                    std::string condition);
```

### `PrintPlan`

```cpp
void PrintPlan(const PlanNode* node, int indent = 0);
```

Output format (2 spaces per indent level):
```
Project [id, name]
  Filter [id > 3] on employees
    Join [employees.id = departments.emp_id]
      Scan [employees]
      Scan [departments]
```

### `PredicatePushdownRule::Apply`

```cpp
class PredicatePushdownRule {
public:
    static std::unique_ptr<PlanNode> Apply(std::unique_ptr<PlanNode> root);
};
```

Rule: if a `FilterNode` sits above a `JoinNode` and `predicate_table` references only **one** of the join's two children, move the `FilterNode` below the `JoinNode`, wrapping the matching child:

```
Filter [pred on A]          →        Join
  Join                                 Filter [pred on A]    B
    A    B                               A
```

Apply recursively until no more rewrites are possible.

## What to Print

```
=== Before pushdown ===
Project [id, name]
  Filter [id > 3] on employees
    Join [employees.id = departments.emp_id]
      Scan [employees]
      Scan [departments]

=== After pushdown ===
Project [id, name]
  Join [employees.id = departments.emp_id]
    Filter [id > 3] on employees
      Scan [employees]
    Scan [departments]
```

## Constraints

- Compile with `g++ -std=c++17 -Wall -Wextra`.
- `PlanNode` must be move-only (owns children via `unique_ptr`).
- No cycles in the plan tree.
