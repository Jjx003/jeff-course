#include <algorithm>
#include <cctype>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

// ---------------------------------------------------------------------------
// Schema and InMemoryTable
// ---------------------------------------------------------------------------

struct Schema {
    std::vector<std::string> columns;

    int ColIndex(const std::string& name) const {
        for (size_t i = 0; i < columns.size(); ++i) {
            if (columns[i] == name) return static_cast<int>(i);
        }
        return -1;
    }
};

class InMemoryTable {
public:
    Schema schema;
    std::vector<std::vector<int64_t>> rows;

    void Insert(std::vector<int64_t> row) {
        rows.push_back(std::move(row));
    }
};

// ---------------------------------------------------------------------------
// Abstract executor
// ---------------------------------------------------------------------------

class AbstractExecutor {
public:
    virtual ~AbstractExecutor() = default;
    virtual void Init() = 0;
    virtual const std::vector<int64_t>* Next() = 0;
    virtual void Close() = 0;
};

// ---------------------------------------------------------------------------
// Predicate operator
// ---------------------------------------------------------------------------

enum class CompareOp { EQ, LT, GT, LEQ, GEQ };

static bool ApplyOp(CompareOp op, int64_t lhs, int64_t rhs) {
    switch (op) {
        case CompareOp::EQ:  return lhs == rhs;
        case CompareOp::LT:  return lhs <  rhs;
        case CompareOp::GT:  return lhs >  rhs;
        case CompareOp::LEQ: return lhs <= rhs;
        case CompareOp::GEQ: return lhs >= rhs;
    }
    return false;
}

// ---------------------------------------------------------------------------
// InMemorySeqScan
// ---------------------------------------------------------------------------

class InMemorySeqScan : public AbstractExecutor {
public:
    InMemorySeqScan(const InMemoryTable& table,
                    int filter_col, CompareOp filter_op, int64_t filter_val,
                    bool has_filter)
        : table_(table), filter_col_(filter_col),
          filter_op_(filter_op), filter_val_(filter_val),
          has_filter_(has_filter), index_(0) {}

    void Init() override { index_ = 0; }

    const std::vector<int64_t>* Next() override {
        while (index_ < table_.rows.size()) {
            const auto& row = table_.rows[index_++];
            if (!has_filter_ ||
                ApplyOp(filter_op_, row[filter_col_], filter_val_)) {
                return &row;
            }
        }
        return nullptr;
    }

    void Close() override {}

private:
    const InMemoryTable& table_;
    int        filter_col_;
    CompareOp  filter_op_;
    int64_t    filter_val_;
    bool       has_filter_;
    size_t     index_;
};

// ---------------------------------------------------------------------------
// Projector
// ---------------------------------------------------------------------------

class Projector : public AbstractExecutor {
public:
    Projector(std::unique_ptr<AbstractExecutor> child,
              std::vector<int> col_indices)
        : child_(std::move(child)), col_indices_(std::move(col_indices)) {}

    void Init() override { child_->Init(); }

    const std::vector<int64_t>* Next() override {
        const auto* row = child_->Next();
        if (!row) return nullptr;
        buf_.clear();
        for (int idx : col_indices_) {
            buf_.push_back((*row)[idx]);
        }
        return &buf_;
    }

    void Close() override { child_->Close(); }

private:
    std::unique_ptr<AbstractExecutor> child_;
    std::vector<int>        col_indices_;
    std::vector<int64_t>    buf_;
};

// ---------------------------------------------------------------------------
// Logical plan
// ---------------------------------------------------------------------------

struct WhereClause {
    bool       present = false;
    std::string col;
    CompareOp  op = CompareOp::EQ;
    int64_t    val = 0;
};

struct LogicalPlan {
    std::string              table_name;
    std::vector<std::string> select_cols;
    WhereClause              where;
};

// ---------------------------------------------------------------------------
// Tokenizer helper
// ---------------------------------------------------------------------------

static std::vector<std::string> Tokenize(const std::string& sql) {
    // Replace commas with spaces so they split naturally
    std::string s = sql;
    std::replace(s.begin(), s.end(), ',', ' ');
    std::istringstream iss(s);
    std::vector<std::string> tokens;
    std::string tok;
    while (iss >> tok) {
        tokens.push_back(tok);
    }
    return tokens;
}

static std::string ToUpper(std::string s) {
    for (char& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

static CompareOp ParseOp(const std::string& s) {
    if (s == "=")  return CompareOp::EQ;
    if (s == "<")  return CompareOp::LT;
    if (s == ">")  return CompareOp::GT;
    if (s == "<=") return CompareOp::LEQ;
    if (s == ">=") return CompareOp::GEQ;
    throw std::runtime_error("Unknown operator: " + s);
}

// ---------------------------------------------------------------------------
// Parser
// ---------------------------------------------------------------------------

LogicalPlan ParseSQL(const std::string& sql) {
    auto tokens = Tokenize(sql);
    LogicalPlan lp;

    // Expect: SELECT col [col ...] FROM table [WHERE col op val]
    size_t i = 0;
    if (i >= tokens.size() || ToUpper(tokens[i]) != "SELECT")
        throw std::runtime_error("Expected SELECT");
    ++i;

    // Collect columns until FROM
    while (i < tokens.size() && ToUpper(tokens[i]) != "FROM") {
        lp.select_cols.push_back(tokens[i++]);
    }
    if (i >= tokens.size() || ToUpper(tokens[i]) != "FROM")
        throw std::runtime_error("Expected FROM");
    ++i;

    // Table name
    if (i >= tokens.size())
        throw std::runtime_error("Expected table name");
    lp.table_name = tokens[i++];

    // Optional WHERE
    if (i < tokens.size() && ToUpper(tokens[i]) == "WHERE") {
        ++i;
        if (i + 2 >= tokens.size())
            throw std::runtime_error("Incomplete WHERE clause");
        lp.where.present = true;
        lp.where.col = tokens[i++];
        lp.where.op  = ParseOp(tokens[i++]);
        lp.where.val = std::stoll(tokens[i++]);
    }

    return lp;
}

// ---------------------------------------------------------------------------
// Physical planner
// ---------------------------------------------------------------------------

std::unique_ptr<AbstractExecutor> BuildPlan(const LogicalPlan& lp,
                                            const InMemoryTable& table) {
    // Resolve filter column index
    int filter_col = -1;
    CompareOp filter_op = CompareOp::EQ;
    int64_t filter_val = 0;
    bool has_filter = lp.where.present;
    if (has_filter) {
        filter_col = table.schema.ColIndex(lp.where.col);
        filter_op  = lp.where.op;
        filter_val = lp.where.val;
    }

    auto scan = std::make_unique<InMemorySeqScan>(
        table, filter_col, filter_op, filter_val, has_filter);

    // Resolve projection column indices
    std::vector<int> proj_indices;
    for (const auto& col : lp.select_cols) {
        proj_indices.push_back(table.schema.ColIndex(col));
    }

    return std::make_unique<Projector>(std::move(scan), std::move(proj_indices));
}

// ---------------------------------------------------------------------------
// Execute and print
// ---------------------------------------------------------------------------

void Execute(const std::string& sql, const InMemoryTable& table) {
    std::cout << "Query: " << sql << "\n";

    LogicalPlan lp = ParseSQL(sql);
    auto root = BuildPlan(lp, table);
    root->Init();

    // Print header
    const auto& cols = lp.select_cols;
    for (size_t i = 0; i < cols.size(); ++i) {
        if (i) std::cout << " | ";
        std::cout << cols[i];
    }
    std::cout << "\n";

    // Print rows
    while (const auto* row = root->Next()) {
        for (size_t i = 0; i < row->size(); ++i) {
            if (i) std::cout << " | ";
            std::cout << (*row)[i];
        }
        std::cout << "\n";
    }

    root->Close();
    std::cout << "\n";
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    InMemoryTable employees;
    employees.schema.columns = {"id", "dept_id", "salary"};
    employees.Insert({1, 1, 70000});
    employees.Insert({2, 2, 90000});
    employees.Insert({3, 1, 55000});
    employees.Insert({4, 3, 120000});
    employees.Insert({5, 2, 85000});
    employees.Insert({6, 1, 60000});
    employees.Insert({7, 3, 110000});
    employees.Insert({8, 2, 95000});

    Execute("SELECT id, salary FROM employees WHERE salary > 80000", employees);
    Execute("SELECT id FROM employees WHERE dept_id = 1", employees);

    return 0;
}
