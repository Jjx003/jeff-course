#include <algorithm>
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
// Returns the estimated fraction [0.0, 1.0] of tuples satisfying col op val.
// Formulas:
//   EQ  -> 1.0 / num_distinct
//   LT  -> (val - min_val) / (max_val - min_val + 1.0)
//   GT  -> (max_val - val) / (max_val - min_val + 1.0)
//   LEQ -> (val - min_val + 1.0) / (max_val - min_val + 1.0)
//   GEQ -> (max_val - val + 1.0) / (max_val - min_val + 1.0)
// Clamp result to [0.0, 1.0]. If column not found, return 1.0.
// ---------------------------------------------------------------------------

double Selectivity(const TableStats& stats, const std::string& col,
                   Op op, int64_t val) {
    // TODO: look up col in stats.columns; compute selectivity using the
    // formula for op; clamp result to [0.0, 1.0] and return it.
    (void)stats; (void)col; (void)op; (void)val;
    return 1.0;
}

// ---------------------------------------------------------------------------
// Plan node
// ---------------------------------------------------------------------------

enum class NodeType { SCAN, FILTER, JOIN };

struct PlanNode {
    NodeType    type;
    std::string table_name;   // SCAN only
    std::string filter_col;   // FILTER only
    Op          filter_op;    // FILTER only
    int64_t     filter_val;   // FILTER only
    std::vector<PlanNode*> children; // 1 child for FILTER, 2 for JOIN
};

// ---------------------------------------------------------------------------
// EstimateCost
// SCAN   -> stats[table_name].num_tuples
// FILTER -> Selectivity(...) * EstimateCost(child)
// JOIN   -> EstimateCost(left) * EstimateCost(right)
// ---------------------------------------------------------------------------

double EstimateCost(const PlanNode* node,
                    const std::map<std::string, TableStats>& all_stats) {
    // TODO: implement cost estimation for SCAN, FILTER, and JOIN nodes.
    (void)node; (void)all_stats;
    return 0.0;
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    // Build statistics for 'orders' and 'customers'
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

    // TODO: print selectivities for (amount > 500) and (status == 1)
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

    // TODO: print plan costs for scan, filter, and join
    std::cout << "Plan cost (scan orders): "
              << EstimateCost(&scan_orders, all_stats) << "\n";
    std::cout << "Plan cost (filter amount>500): "
              << EstimateCost(&filter_amount, all_stats) << "\n";
    std::cout << "Plan cost (join orders x customers): "
              << EstimateCost(&join_node, all_stats) << "\n";

    return 0;
}
