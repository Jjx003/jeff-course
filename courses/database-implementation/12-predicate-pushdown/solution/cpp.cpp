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
    auto n = std::make_unique<PlanNode>();
    n->type = NodeType::Scan;
    n->table_name = std::move(table);
    return n;
}

std::unique_ptr<PlanNode> MakeFilter(std::unique_ptr<PlanNode> child,
                                      std::string pred, std::string pred_table) {
    auto n = std::make_unique<PlanNode>();
    n->type = NodeType::Filter;
    n->predicate_str   = std::move(pred);
    n->predicate_table = std::move(pred_table);
    n->child = std::move(child);
    return n;
}

std::unique_ptr<PlanNode> MakeProject(std::unique_ptr<PlanNode> child,
                                       std::vector<std::string> cols) {
    auto n = std::make_unique<PlanNode>();
    n->type = NodeType::Project;
    n->cols  = std::move(cols);
    n->child = std::move(child);
    return n;
}

std::unique_ptr<PlanNode> MakeJoin(std::unique_ptr<PlanNode> left,
                                    std::unique_ptr<PlanNode> right,
                                    std::string condition) {
    auto n = std::make_unique<PlanNode>();
    n->type  = NodeType::Join;
    n->join_condition = std::move(condition);
    n->left  = std::move(left);
    n->right = std::move(right);
    return n;
}

// ---------------------------------------------------------------------------
// PrintPlan
// ---------------------------------------------------------------------------

void PrintPlan(const PlanNode* node, int indent = 0) {
    std::string pad(indent * 2, ' ');
    switch (node->type) {
        case NodeType::Scan:
            std::cout << pad << "Scan [" << node->table_name << "]\n";
            break;
        case NodeType::Filter:
            std::cout << pad << "Filter [" << node->predicate_str
                      << "] on " << node->predicate_table << "\n";
            PrintPlan(node->child.get(), indent + 1);
            break;
        case NodeType::Project: {
            std::cout << pad << "Project [";
            for (size_t i = 0; i < node->cols.size(); ++i) {
                if (i) std::cout << ", ";
                std::cout << node->cols[i];
            }
            std::cout << "]\n";
            PrintPlan(node->child.get(), indent + 1);
            break;
        }
        case NodeType::Join:
            std::cout << pad << "Join [" << node->join_condition << "]\n";
            PrintPlan(node->left.get(),  indent + 1);
            PrintPlan(node->right.get(), indent + 1);
            break;
    }
}

// ---------------------------------------------------------------------------
// PredicatePushdownRule
// ---------------------------------------------------------------------------

static std::string RootTable(const PlanNode* node) {
    switch (node->type) {
        case NodeType::Scan:    return node->table_name;
        case NodeType::Filter:  return RootTable(node->child.get());
        case NodeType::Project: return RootTable(node->child.get());
        default:                return "";
    }
}

class PredicatePushdownRule {
public:
    static std::unique_ptr<PlanNode> Apply(std::unique_ptr<PlanNode> root) {
        if (!root) return root;

        if (root->type == NodeType::Filter && root->child &&
            root->child->type == NodeType::Join) {
            auto& join = root->child;
            std::string left_table  = RootTable(join->left.get());
            std::string right_table = RootTable(join->right.get());
            const std::string& pt = root->predicate_table;

            if (!left_table.empty() && pt == left_table) {
                auto new_left = MakeFilter(std::move(join->left),
                                           root->predicate_str, root->predicate_table);
                join->left = Apply(std::move(new_left));
                return Apply(std::move(join));
            } else if (!right_table.empty() && pt == right_table) {
                auto new_right = MakeFilter(std::move(join->right),
                                            root->predicate_str, root->predicate_table);
                join->right = Apply(std::move(new_right));
                return Apply(std::move(join));
            }
        }

        // Recurse
        if (root->child) root->child = Apply(std::move(root->child));
        if (root->left)  root->left  = Apply(std::move(root->left));
        if (root->right) root->right = Apply(std::move(root->right));
        return root;
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
