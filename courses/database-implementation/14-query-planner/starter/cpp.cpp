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

    // Returns the index of column `name`, or -1 if not found.
    int ColIndex(const std::string& name) const {
        // TODO: linear search through columns, return index or -1
        (void)name;
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
// Abstract executor (Volcano / pull model)
// ---------------------------------------------------------------------------

class AbstractExecutor {
public:
    virtual ~AbstractExecutor() = default;
    virtual void Init() = 0;
    // Returns pointer to current row, nullptr when exhausted.
    virtual const std::vector<int64_t>* Next() = 0;
    virtual void Close() = 0;
};

// ---------------------------------------------------------------------------
// Predicate operator
// ---------------------------------------------------------------------------

enum class CompareOp { EQ, LT, GT, LEQ, GEQ };

// Returns true if `lhs op rhs` holds.
static bool ApplyOp(CompareOp op, int64_t lhs, int64_t rhs) {
    // TODO: implement comparison dispatch
    (void)op; (void)lhs; (void)rhs;
    return false;
}

// ---------------------------------------------------------------------------
// InMemorySeqScan
// Iterates all rows in `table`; optionally filters by a single predicate.
// ---------------------------------------------------------------------------

class InMemorySeqScan : public AbstractExecutor {
public:
    InMemorySeqScan(const InMemoryTable& table,
                    int filter_col, CompareOp filter_op, int64_t filter_val,
                    bool has_filter)
        : table_(table), filter_col_(filter_col),
          filter_op_(filter_op), filter_val_(filter_val),
          has_filter_(has_filter), index_(0) {}

    void Init() override {
        // TODO: reset cursor to beginning
        index_ = 0;
    }

    const std::vector<int64_t>* Next() override {
        // TODO: advance cursor; skip rows that fail the filter;
        // return pointer to matching row, or nullptr when exhausted
        (void)filter_col_; (void)filter_op_; (void)filter_val_; (void)has_filter_;
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
// Wraps a child executor; returns only the specified columns.
// ---------------------------------------------------------------------------

class Projector : public AbstractExecutor {
public:
    Projector(std::unique_ptr<AbstractExecutor> child,
              std::vector<int> col_indices)
        : child_(std::move(child)), col_indices_(std::move(col_indices)) {}

    void Init() override { child_->Init(); }

    const std::vector<int64_t>* Next() override {
        // TODO: fetch next row from child; copy only col_indices_ columns
        // into buf_; return &buf_, or nullptr if child is exhausted
        return nullptr;
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
// Tokenizer helpers
// ---------------------------------------------------------------------------

static std::vector<std::string> Tokenize(const std::string& sql) {
    // TODO: replace commas with spaces, then split on whitespace into tokens
    std::string s = sql;
    std::replace(s.begin(), s.end(), ',', ' ');
    std::istringstream iss(s);
    std::vector<std::string> tokens;
    std::string tok;
    while (iss >> tok) tokens.push_back(tok);
    return tokens;
}

static std::string ToUpper(std::string s) {
    for (char& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

static CompareOp ParseOp(const std::string& s) {
    // TODO: map "=", "<", ">", "<=", ">=" to CompareOp
    if (s == "=")  return CompareOp::EQ;
    if (s == "<")  return CompareOp::LT;
    if (s == ">")  return CompareOp::GT;
    if (s == "<=") return CompareOp::LEQ;
    if (s == ">=") return CompareOp::GEQ;
    throw std::runtime_error("Unknown operator: " + s);
}

// ---------------------------------------------------------------------------
// Parser
// Parses: SELECT col [, col]* FROM table [WHERE col op int_val]
// ---------------------------------------------------------------------------

LogicalPlan ParseSQL(const std::string& sql) {
    // TODO: tokenize; consume SELECT, columns, FROM, table, optional WHERE clause
    auto tokens = Tokenize(sql);
    LogicalPlan lp;
    size_t i = 0;
    (void)tokens; (void)i;
    return lp;
}

// ---------------------------------------------------------------------------
// Physical planner
// Resolves column indices and constructs the executor tree.
// ---------------------------------------------------------------------------

std::unique_ptr<AbstractExecutor> BuildPlan(const LogicalPlan& lp,
                                            const InMemoryTable& table) {
    // TODO:
    // 1. Resolve filter column index (if WHERE is present)
    // 2. Construct InMemorySeqScan
    // 3. Resolve projection column indices
    // 4. Wrap with Projector and return
    (void)lp; (void)table;
    return nullptr;
}

// ---------------------------------------------------------------------------
// Execute and print
// ---------------------------------------------------------------------------

void Execute(const std::string& sql, const InMemoryTable& table) {
    // TODO: parse, build plan, init, print header, iterate and print rows,
    // close, print blank line
    std::cout << "Query: " << sql << "\n";
    (void)table;
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
