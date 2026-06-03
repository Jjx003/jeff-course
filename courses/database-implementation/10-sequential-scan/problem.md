# Sequential Scan Executor

## Your Task

Implement the Volcano (iterator) execution model: `AbstractExecutor`, a `TableHeap` backed by the buffer pool and slotted pages, and `SeqScanExecutor`.

### `AbstractExecutor`

```cpp
class AbstractExecutor {
public:
    virtual ~AbstractExecutor() = default;
    virtual void   Init()  = 0;
    virtual Tuple* Next()  = 0;   // returns nullptr when exhausted
    virtual void   Close() = 0;
};
```

### `TableHeap`

A heap file: a linked list of pages, each formatted as a slotted page. Uses the buffer pool to access pages.

```cpp
class TableHeap {
public:
    TableHeap(BufferPoolManager* bpm, const Schema& schema);

    // Append a tuple to the last page (or allocate new page if full).
    // Returns {page_id, slot_id}.
    std::pair<page_id_t, int> InsertTuple(const Tuple& tuple);

    // Iterator over all non-deleted tuples.
    struct Iterator {
        bool operator!=(const Iterator& o) const;
        Iterator& operator++();
        Tuple operator*() const;
    };
    Iterator Begin() const;
    Iterator End()   const;
};
```

For this module, simplify `TableHeap` to keep all tuples in a `std::vector<Tuple>` (no actual page I/O for tuples — that integration is left as an extension). Focus the complexity on the executor model.

### `SeqScanExecutor`

```cpp
using Predicate = std::function<bool(const Tuple&, const Schema&)>;

class SeqScanExecutor : public AbstractExecutor {
public:
    SeqScanExecutor(TableHeap* table, const Schema& schema,
                    Predicate pred = nullptr);

    void   Init()  override;
    Tuple* Next()  override;
    void   Close() override;
};
```

`Init()` resets the iterator to the beginning. `Next()` advances past tuples that fail the predicate. Returns `nullptr` at end.

## What to Print

```
All tuples:
1 | 10.000000 | Alice
2 | 20.000000 | Bob
3 | 30.000000 | Carol
4 | 40.000000 | Dave
5 | 50.000000 | Eve

Tuples with id > 2:
3 | 30.000000 | Carol
4 | 40.000000 | Dave
5 | 50.000000 | Eve
```

Schema: `id INT32, score FLOAT64, name VARCHAR`. Insert 5 tuples as above.

## Constraints

- Compile with `g++ -std=c++17 -Wall -Wextra`.
- Include the `Schema`, `Value`, `Tuple` implementations from module 09.
- The `TableHeap` in the solution may use `std::vector<Tuple>` internally for simplicity.
- The predicate receives the tuple and schema; access `id` via `t.GetValue(schema, 0).AsInt32()`.
