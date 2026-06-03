# Query Planner: Running Basic SELECT

## Your Task

Build a minimal end-to-end query engine: tokenize SQL, build a logical plan, instantiate
physical operators, execute, and print results.

---

### 1. Grammar

Support exactly this subset of SQL:

```
SELECT <col> [, <col>]* FROM <table> [WHERE <col> <op> <int_val>]
```

Operators: `=`, `<`, `>`, `<=`, `>=`

No subqueries, no aggregates, no joins.

---

### 2. In-Memory Table

```cpp
struct Schema {
    std::vector<std::string> columns; // ordered column names
    int ColIndex(const std::string& name) const; // -1 if not found
};

class InMemoryTable {
public:
    Schema schema;
    std::vector<std::vector<int64_t>> rows;

    void Insert(std::vector<int64_t> row);
};
```

Rows are stored as `vector<int64_t>`.  Column positions are determined by `Schema`.

---

### 3. Abstract Executor Interface

```cpp
class AbstractExecutor {
public:
    virtual ~AbstractExecutor() = default;
    virtual void Init() = 0;
    // Returns a pointer to the current row, or nullptr when exhausted.
    virtual const std::vector<int64_t>* Next() = 0;
    virtual void Close() = 0;
};
```

---

### 4. Physical Operators

**`InMemorySeqScan`** — iterates all rows; optionally applies a WHERE filter inline.

```cpp
class InMemorySeqScan : public AbstractExecutor {
    // Holds a reference to the table, an optional filter column index,
    // operator, and value. Returns rows one by one, skipping those that
    // fail the filter.
};
```

**`Projector`** — wraps a child executor, returns only the specified column indices.

```cpp
class Projector : public AbstractExecutor {
    // Wraps a child executor; on each Next() call, fetches from child
    // and copies only the requested columns into an internal row buffer.
};
```

---

### 5. Logical Plan Struct

```cpp
enum class CompareOp { EQ, LT, GT, LEQ, GEQ };

struct WhereClause {
    bool        present;
    std::string col;
    CompareOp   op;
    int64_t     val;
};

struct LogicalPlan {
    std::string              table_name;
    std::vector<std::string> select_cols;
    WhereClause              where;
};
```

---

### 6. Parser

```cpp
LogicalPlan ParseSQL(const std::string& sql);
```

Tokenize by splitting on whitespace and `,`.  Handle two-character operators (`<=`, `>=`)
by checking if the next character is `=` after seeing `<` or `>`.  Parsing is
case-insensitive for keywords (`SELECT`, `FROM`, `WHERE`).

---

### 7. Physical Planner

```cpp
std::unique_ptr<AbstractExecutor> BuildPlan(const LogicalPlan& lp,
                                            const InMemoryTable& table);
```

1. Resolve column indices from `table.schema`.
2. Construct `InMemorySeqScan` with the filter (if any).
3. Wrap with `Projector` for the SELECT columns.
4. Return the root executor.

---

### 8. Execution + Output

```cpp
void Execute(const std::string& sql, const InMemoryTable& table);
```

Parse → plan → execute.  Print:

```
Query: <sql>
<col1> | <col2> | ...    ← header, single column has no pipes
<val> | <val> | ...      ← one line per result row
                         ← blank line after each query
```

---

### 9. Demo `main()`

Create table `employees(id, dept_id, salary)` with 8 rows:

| id | dept_id | salary |
|----|---------|--------|
| 1  | 1       | 70000  |
| 2  | 2       | 90000  |
| 3  | 1       | 55000  |
| 4  | 3       | 120000 |
| 5  | 2       | 85000  |
| 6  | 1       | 60000  |
| 7  | 3       | 110000 |
| 8  | 2       | 95000  |

Run:
```sql
SELECT id, salary FROM employees WHERE salary > 80000
SELECT id FROM employees WHERE dept_id = 1
```

Expected output:
```
Query: SELECT id, salary FROM employees WHERE salary > 80000
id | salary
2 | 90000
4 | 120000
5 | 85000
7 | 110000
8 | 95000

Query: SELECT id FROM employees WHERE dept_id = 1
id
1
3
6

```

## Constraints

- Compile with `g++ -std=c++17 -Wall -Wextra`.
- Use only the C++ standard library.
- The parser must handle the two queries above correctly.
- Do not use `std::regex` — tokenize by hand.
