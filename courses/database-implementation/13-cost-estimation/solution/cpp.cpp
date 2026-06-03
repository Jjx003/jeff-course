#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <string>
#include <unordered_map>
#include <vector>

// ---------------------------------------------------------------------------
// Column and Table Statistics
// ---------------------------------------------------------------------------

struct ColumnStats {
    int64_t min_val;
    int64_t max_val;
    size_t  num_distinct;
};

struct TableStats {
    size_t num_tuples;
    std::unordered_map<std::string, ColumnStats> columns;
};

// ---------------------------------------------------------------------------
// Predicate operator
// ---------------------------------------------------------------------------

enum class Op { EQ, LT, GT, LEQ, GEQ };

// ---------------------------------------------------------------------------
// Selectivity
// ---------------------------------------------------------------------------

double Selectivity(const TableStats& stats, const std::string& col,
                   Op op, int64_t val) {
    auto it = stats.columns.find(col);
    if (it == stats.columns.end()) return 1.0;

    const ColumnStats& cs = it->second;
    double range = static_cast<double>(cs.max_val - cs.min_val + 1);
    double result = 0.0;

    switch (op) {
        case Op::EQ:
            if (cs.num_distinct == 0) return 0.0;
            result = 1.0 / static_cast<double>(cs.num_distinct);
            break;
        case Op::LT:
            result = (val - cs.min_val) / range;
            break;
        case Op::GT:
            result = (cs.max_val - val) / range;
            break;
        case Op::LEQ:
            result = (val - cs.min_val + 1.0) / range;
            break;
        case Op::GEQ:
            result = (cs.max_val - val + 1.0) / range;
            break;
    }
    return std::clamp(result, 0.0, 1.0);
}

// ---------------------------------------------------------------------------
// Plan node
// ---------------------------------------------------------------------------

enum class NodeType { SCAN, FILTER, JOIN };

struct PlanNode {
    NodeType    type;
    std::string table_name;   // SCAN
    std::string filter_col;   // FILTER
    Op          filter_op;    // FILTER
    int64_t     filter_val;   // FILTER
    std::vector<PlanNode*> children; // 1 for FILTER, 2 for JOIN
};

// ---------------------------------------------------------------------------
// EstimateCost
// ---------------------------------------------------------------------------

double EstimateCost(const PlanNode* node,
                    const std::map<std::string, TableStats>& all_stats) {
    switch (node->type) {
        case NodeType::SCAN: {
            auto it = all_stats.find(node->table_name);
            if (it == all_stats.end()) return 0.0;
            return static_cast<double>(it->second.num_tuples);
        }
        case NodeType::FILTER: {
            auto it = all_stats.find(node->children[0]->table_name);
            if (it == all_stats.end()) return 0.0;
            double sel = Selectivity(it->second, node->filter_col,
                                     node->filter_op, node->filter_val);
            return sel * EstimateCost(node->children[0], all_stats);
        }
        case NodeType::JOIN: {
            return EstimateCost(node->children[0], all_stats)
                 * EstimateCost(node->children[1], all_stats);
        }
    }
    return 0.0;
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    // Build statistics
    TableStats orders_stats;
    orders_stats.num_tuples = 10000;
    orders_stats.columns["amount"] = ColumnStats{1, 1000, 1000};
    orders_stats.columns["status"] = ColumnStats{1, 10, 10};

    TableStats customers_stats;
    customers_stats.num_tuples = 100;

    std::map<std::string, TableStats> all_stats{
        {"orders",    orders_stats},
        {"customers", customers_stats}
    };

    // Print table summary
    std::cout << "Table 'orders': " << orders_stats.num_tuples << " tuples\n";

    // Selectivity examples
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "Selectivity(amount > 500): "
              << Selectivity(orders_stats, "amount", Op::GT, 500) << "\n";
    std::cout << "Selectivity(status == 1): "
              << Selectivity(orders_stats, "status", Op::EQ, 1) << "\n";

    // Build plan nodes
    PlanNode scan_orders{NodeType::SCAN, "orders", "", Op::EQ, 0, {}};
    PlanNode scan_customers{NodeType::SCAN, "customers", "", Op::EQ, 0, {}};
    PlanNode filter_amount{NodeType::FILTER, "", "amount", Op::GT, 500,
                           {&scan_orders}};
    PlanNode join_node{NodeType::JOIN, "", "", Op::EQ, 0,
                       {&filter_amount, &scan_customers}};

    // Cost estimates
    std::cout << "Plan cost (scan orders): "
              << EstimateCost(&scan_orders, all_stats) << "\n";
    std::cout << "Plan cost (filter amount>500): "
              << EstimateCost(&filter_amount, all_stats) << "\n";
    std::cout << "Plan cost (join orders x customers): "
              << EstimateCost(&join_node, all_stats) << "\n";

    return 0;
}
