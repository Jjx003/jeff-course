# Tips & Notes

## SeqScanExecutor state

```cpp
class SeqScanExecutor : public AbstractExecutor {
    TableHeap*  table_;
    const Schema& schema_;
    Predicate   pred_;
    size_t      idx_{0};
    Tuple       current_;
public:
    void Init()  override { idx_ = 0; }
    Tuple* Next() override {
        while (idx_ < table_->Size()) {
            current_ = table_->GetTuple(idx_++);
            if (!pred_ || pred_(current_, schema_)) return &current_;
        }
        return nullptr;
    }
    void Close() override {}
};
```

## Printing all rows with an executor

```cpp
void PrintAll(AbstractExecutor& exec, const Schema& schema) {
    exec.Init();
    while (Tuple* t = exec.Next()) {
        for (size_t i = 0; i < schema.NumColumns(); ++i) {
            if (i > 0) std::cout << " | ";
            std::cout << t->GetValue(schema, i).ToString();
        }
        std::cout << "\n";
    }
    exec.Close();
}
```

## Predicate construction

```cpp
Predicate p = [](const Tuple& t, const Schema& s) {
    return t.GetValue(s, 0).AsInt32() > 2;
};
SeqScanExecutor filtered(&heap, schema, p);
```

## TableHeap simplification

For this module, backing `TableHeap` with `std::vector<Tuple>` is intentional. The purpose is to validate the executor interface — the buffer pool integration is already covered in module 06. If you want to connect them, `InsertTuple` can serialize the tuple bytes into a slotted page via the buffer pool; `Begin/End` iterates pages and slots.

## Why `Tuple*` not `std::optional<Tuple>`?

Returning a pointer to an internal buffer (`current_`) avoids a copy per `Next()` call. The pointer is valid until the next `Next()` call — the same lifetime semantics as a C++ input iterator's dereference. Callers that need to retain a tuple must copy it.

This is the same convention used in Apache Arrow's `RecordBatch` and DuckDB's `DataChunk` — the executor owns the output buffer, the consumer must copy if it needs persistence.

## Multiple scans

`Init()` must reset `idx_ = 0` so the executor can be used multiple times. This is required when a nested-loop join re-opens the inner child for each outer tuple.
