#include <cstddef>
#include <cstdint>
#include <cstring>
#include <functional>
#include <initializer_list>
#include <iostream>
#include <string>
#include <utility>
#include <variant>
#include <vector>

// ---- TypeId / Column / Schema / Value / Tuple (same as module 09) ----------

enum class TypeId { INT32, INT64, FLOAT64, VARCHAR };

static size_t TypeSize(TypeId t) {
    switch (t) {
        case TypeId::INT32:   return 4;
        case TypeId::INT64:   return 8;
        case TypeId::FLOAT64: return 8;
        case TypeId::VARCHAR: return 4;
    }
    return 0;
}

struct Column { std::string name; TypeId type; size_t offset; size_t size; };

class Schema {
public:
    Schema(std::initializer_list<std::pair<std::string, TypeId>> cols) {
        size_t off = 0;
        for (auto& [n, t] : cols) {
            size_t sz = TypeSize(t);
            columns_.push_back({n, t, off, sz});
            off += sz;
        }
        tuple_size_ = off;
    }
    const Column& GetColumn(size_t i) const { return columns_[i]; }
    size_t        NumColumns()         const { return columns_.size(); }
    size_t        TupleSize()          const { return tuple_size_; }
private:
    std::vector<Column> columns_;
    size_t              tuple_size_{0};
};

class Value {
public:
    explicit Value(int32_t v)     : type_(TypeId::INT32),   data_(v) {}
    explicit Value(int64_t v)     : type_(TypeId::INT64),   data_(v) {}
    explicit Value(double v)      : type_(TypeId::FLOAT64), data_(v) {}
    explicit Value(std::string v) : type_(TypeId::VARCHAR), data_(std::move(v)) {}
    TypeId      Type()     const { return type_; }
    std::string ToString() const {
        return std::visit([](auto&& v) -> std::string {
            using T = std::decay_t<decltype(v)>;
            if constexpr (std::is_same_v<T, std::string>) return v;
            else return std::to_string(v);
        }, data_);
    }
    int32_t     AsInt32()   const { return std::get<int32_t>(data_); }
    int64_t     AsInt64()   const { return std::get<int64_t>(data_); }
    double      AsFloat64() const { return std::get<double>(data_); }
    std::string AsVarchar() const { return std::get<std::string>(data_); }
private:
    TypeId type_;
    std::variant<int32_t, int64_t, double, std::string> data_;
};

class Tuple {
public:
    Tuple() = default;
    Tuple(const Schema& schema, std::initializer_list<Value> values) {
        data_.resize(schema.TupleSize());
        size_t i = 0;
        for (const Value& v : values) {
            const Column& col = schema.GetColumn(i++);
            switch (col.type) {
                case TypeId::INT32:   { int32_t x=v.AsInt32();   std::memcpy(data_.data()+col.offset,&x,4); break; }
                case TypeId::INT64:   { int64_t x=v.AsInt64();   std::memcpy(data_.data()+col.offset,&x,8); break; }
                case TypeId::FLOAT64: { double  x=v.AsFloat64(); std::memcpy(data_.data()+col.offset,&x,8); break; }
                case TypeId::VARCHAR: {
                    uint32_t voff=static_cast<uint32_t>(data_.size()-schema.TupleSize());
                    std::memcpy(data_.data()+col.offset,&voff,4);
                    for(char c:v.AsVarchar()) data_.push_back(static_cast<std::byte>(c));
                    data_.push_back(std::byte{0}); break;
                }
            }
        }
    }
    Value GetValue(const Schema& schema, size_t col_idx) const {
        const Column& col = schema.GetColumn(col_idx);
        switch (col.type) {
            case TypeId::INT32:   { int32_t x; std::memcpy(&x,data_.data()+col.offset,4); return Value{x}; }
            case TypeId::INT64:   { int64_t x; std::memcpy(&x,data_.data()+col.offset,8); return Value{x}; }
            case TypeId::FLOAT64: { double  x; std::memcpy(&x,data_.data()+col.offset,8); return Value{x}; }
            case TypeId::VARCHAR: {
                uint32_t voff; std::memcpy(&voff,data_.data()+col.offset,4);
                const char* s=reinterpret_cast<const char*>(data_.data()+schema.TupleSize()+voff);
                return Value{std::string(s)};
            }
        }
        return Value{int32_t{0}};
    }
    const std::vector<std::byte>& Data() const { return data_; }
private:
    std::vector<std::byte> data_;
};

// ---------------------------------------------------------------------------
// TableHeap — store tuples (simplified: vector-backed)
// ---------------------------------------------------------------------------

class TableHeap {
public:
    explicit TableHeap(const Schema& schema) : schema_(schema) {}

    void InsertTuple(const Tuple& t) { tuples_.push_back(t); }
    size_t Size()                   const { return tuples_.size(); }
    const Tuple& GetTuple(size_t i) const { return tuples_[i]; }
    const Schema& GetSchema()        const { return schema_; }

private:
    const Schema&      schema_;
    std::vector<Tuple> tuples_;
};

// ---------------------------------------------------------------------------
// AbstractExecutor
// ---------------------------------------------------------------------------

class AbstractExecutor {
public:
    virtual ~AbstractExecutor() = default;
    virtual void   Init()  = 0;
    virtual Tuple* Next()  = 0;   // nullptr when done
    virtual void   Close() = 0;
};

// ---------------------------------------------------------------------------
// SeqScanExecutor — TODO: implement Init, Next, Close
// ---------------------------------------------------------------------------

using Predicate = std::function<bool(const Tuple&, const Schema&)>;

class SeqScanExecutor : public AbstractExecutor {
public:
    SeqScanExecutor(TableHeap* table, const Schema& schema, Predicate pred = nullptr)
        : table_(table), schema_(schema), pred_(std::move(pred)) {}

    void Init() override {
        // TODO: reset idx_ to 0
    }

    Tuple* Next() override {
        // TODO: advance idx_ until a tuple passes pred_ (or pred_ is null)
        //       store it in current_ and return &current_
        //       return nullptr when idx_ >= table_->Size()
        return nullptr;
    }

    void Close() override {
        // nothing to do
    }

private:
    TableHeap*    table_;
    const Schema& schema_;
    Predicate     pred_;
    size_t        idx_{0};
    Tuple         current_;
};

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    Schema schema{
        {"id",    TypeId::INT32},
        {"score", TypeId::FLOAT64},
        {"name",  TypeId::VARCHAR},
    };

    TableHeap heap(schema);
    heap.InsertTuple(Tuple(schema, {Value{int32_t{1}}, Value{10.0}, Value{std::string{"Alice"}}}));
    heap.InsertTuple(Tuple(schema, {Value{int32_t{2}}, Value{20.0}, Value{std::string{"Bob"}}}));
    heap.InsertTuple(Tuple(schema, {Value{int32_t{3}}, Value{30.0}, Value{std::string{"Carol"}}}));
    heap.InsertTuple(Tuple(schema, {Value{int32_t{4}}, Value{40.0}, Value{std::string{"Dave"}}}));
    heap.InsertTuple(Tuple(schema, {Value{int32_t{5}}, Value{50.0}, Value{std::string{"Eve"}}}));

    std::cout << "All tuples:\n";
    SeqScanExecutor full_scan(&heap, schema);
    PrintAll(full_scan, schema);

    std::cout << "\nTuples with id > 2:\n";
    Predicate pred = [](const Tuple& t, const Schema& s) {
        return t.GetValue(s, 0).AsInt32() > 2;
    };
    SeqScanExecutor filtered(&heap, schema, pred);
    PrintAll(filtered, schema);

    return 0;
}
