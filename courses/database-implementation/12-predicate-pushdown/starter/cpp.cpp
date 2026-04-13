#include <iostream>
#include <memory>
#include <string>
#include <vector>

// ---------------------------------------------------------------------------
// Plan node types
// ---------------------------------------------------------------------------

enum class NodeType { Scan, Filter, Project, Join };

struct PlanNode {
    NodeType    type;
    std::string table_name;
    std::string predicate_str;
    std::string predicate_table;
    std::vector<std::string> cols;
    std::string join_condition;
    std::unique_ptr<PlanNode> child;
    std::unique_ptr<PlanNode> left;
    std::unique_ptr<PlanNode> right;
};

std::unique_ptr<PlanNode> MakeScan(std::string table) {
    // TODO: allocate a PlanNode, set type = NodeType::Scan and table_name,
    // return it
    auto n = std::make_unique<PlanNode>();
    n->type = NodeType::Scan;
    n->table_name = std::move(table);
    return n;
}

std::unique_ptr<PlanNode> MakeFilter(std::unique_ptr<PlanNode> child,
                                      std::string pred, std::string pred_table) {
    // TODO: allocate a PlanNode, set type = NodeType::Filter, predicate_str,
    // predicate_table, and child; return it
    auto n = std::make_unique<PlanNode>();
    n->type = NodeType::Filter;
    n->predicate_str   = std::move(pred);
    n->predicate_table = std::move(pred_table);
    n->child = std::move(child);
    return n;
}

std::unique_ptr<PlanNode> MakeProject(std::unique_ptr<PlanNode> child,
                                       std::vector<std::string> cols) {
    // TODO: allocate a PlanNode, set type = NodeType::Project, cols, and child;
    // return it
    auto n = std::make_unique<PlanNode>();
    n->type = NodeType::Project;
    n->cols  = std::move(cols);
    n->child = std::move(child);
    return n;
}

std::unique_ptr<PlanNode> MakeJoin(std::unique_ptr<PlanNode> left,
                                    std::unique_ptr<PlanNode> right,
                                    std::string condition) {
    // TODO: allocate a PlanNode, set type = NodeType::Join, join_condition,
    // left, and right; return it
    auto n = std::make_unique<PlanNode>();
    n->type  = NodeType::Join;
    n->join_condition = std::move(condition);
    n->left  = std::move(left);
    n->right = std::move(right);
    return n;
}

// ---------------------------------------------------------------------------
// PrintPlan — prints the plan tree with 2-space indentation per level
// ---------------------------------------------------------------------------

void PrintPlan(const PlanNode* node, int indent = 0) {
    // TODO: print each node type using the format:
    //   Scan  → "Scan [table_name]"
    //   Filter → "Filter [predicate_str] on predicate_table"
    //   Project → "Project [col1, col2, ...]"
    //   Join  → "Join [join_condition]"
    // Recurse into children with indent + 1 (2 spaces per level)
    (void)node; (void)indent;
}

// ---------------------------------------------------------------------------
// Helper: walk down child/left pointers to find the root table name
// ---------------------------------------------------------------------------

static std::string RootTable(const PlanNode* node) {
    // TODO: return the table_name of the deepest Scan reachable via
    // child/left pointers; return "" for Join nodes
    (void)node;
    return "";
}

// ---------------------------------------------------------------------------
// PredicatePushdownRule
// ---------------------------------------------------------------------------

class PredicatePushdownRule {
public:
    // TODO: If root is a Filter whose child is a Join, and predicate_table
    // matches one side of the join, push the Filter below the Join onto that
    // side. Recurse until no more rewrites are possible.
    static std::unique_ptr<PlanNode> Apply(std::unique_ptr<PlanNode> root) {
        (void)root;
        return nullptr;
    }
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    // Build plan: Project → Filter → Join → (Scan, Scan)
    auto plan = MakeProject(
        MakeFilter(
            MakeJoin(
                MakeScan("employees"),
                MakeScan("departments"),
                "employees.id = departments.emp_id"
            ),
            "id > 3",
            "employees"
        ),
        {"id", "name"}
    );

    std::cout << "=== Before pushdown ===\n";
    PrintPlan(plan.get());

    plan = PredicatePushdownRule::Apply(std::move(plan));

    std::cout << "\n=== After pushdown ===\n";
    PrintPlan(plan.get());

    return 0;
}
