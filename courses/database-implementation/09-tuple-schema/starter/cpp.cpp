#include <cstddef>
#include <cstdint>
#include <cstring>
#include <initializer_list>
#include <iostream>
#include <string>
#include <utility>
#include <variant>
#include <vector>

// ---------------------------------------------------------------------------
// TypeId
// ---------------------------------------------------------------------------

enum class TypeId { INT32, INT64, FLOAT64, VARCHAR };

static size_t TypeSize(TypeId t) {
    // TODO: INT32→4, INT64→8, FLOAT64→8, VARCHAR→4 (length prefix)
    (void)t; return 0;
}

static std::string TypeName(TypeId t) {
    // TODO: return human-readable string
    (void)t; return "";
}

// ---------------------------------------------------------------------------
// Column / Schema
// ---------------------------------------------------------------------------

struct Column {
    std::string name;
    TypeId      type;
    size_t      offset;
    size_t      size;
};

class Schema {
public:
    // Compute offsets for each column sequentially
    Schema(std::initializer_list<std::pair<std::string, TypeId>> cols) {
        // TODO: iterate cols, assign offsets, fill columns_, set tuple_size_
    }

    const Column& GetColumn(size_t idx) const { return columns_[idx]; }
    size_t        NumColumns()           const { return columns_.size(); }
    size_t        TupleSize()            const { return tuple_size_; }

private:
    std::vector<Column> columns_;
    size_t              tuple_size_{0};
};

// ---------------------------------------------------------------------------
// Value
// ---------------------------------------------------------------------------

class Value {
public:
    explicit Value(int32_t v)     : type_(TypeId::INT32),   data_(v) {}
    explicit Value(int64_t v)     : type_(TypeId::INT64),   data_(v) {}
    explicit Value(double v)      : type_(TypeId::FLOAT64), data_(v) {}
    explicit Value(std::string v) : type_(TypeId::VARCHAR), data_(std::move(v)) {}

    TypeId Type() const { return type_; }

    std::string ToString() const {
        // TODO: use std::visit to convert each alternative to string
        return "";
    }

    int32_t     AsInt32()   const { return std::get<int32_t>(data_); }
    int64_t     AsInt64()   const { return std::get<int64_t>(data_); }
    double      AsFloat64() const { return std::get<double>(data_); }
    std::string AsVarchar() const { return std::get<std::string>(data_); }

private:
    TypeId type_;
    std::variant<int32_t, int64_t, double, std::string> data_;
};

// ---------------------------------------------------------------------------
// Tuple
// ---------------------------------------------------------------------------

class Tuple {
public:
    Tuple() = default;

    // Serialize values into data_ according to schema layout
    Tuple(const Schema& schema, std::initializer_list<Value> values) {
        // TODO:
        // resize data_ to schema.TupleSize() (fixed region)
        // for each column:
        //   INT32/INT64/FLOAT64: memcpy into data_[col.offset]
        //   VARCHAR: record var_off = current variable-section size,
        //            write var_off as uint32_t at col.offset,
        //            append string bytes + null terminator to data_
    }

    // Deserialize column col_idx from data_
    Value GetValue(const Schema& schema, size_t col_idx) const {
        // TODO: switch on type, memcpy from data_[col.offset]
        //       for VARCHAR: read var_off, point into variable section
        return Value{int32_t{0}};
    }

    const std::vector<std::byte>& Data() const { return data_; }

private:
    std::vector<std::byte> data_;
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    Schema schema{
        {"id",    TypeId::INT32},
        {"score", TypeId::FLOAT64},
        {"name",  TypeId::VARCHAR},
    };

    // Print schema
    std::cout << "Schema:";
    for (size_t i = 0; i < schema.NumColumns(); ++i) {
        const Column& c = schema.GetColumn(i);
        std::cout << " " << c.name << " " << TypeName(c.type);
        if (i + 1 < schema.NumColumns()) std::cout << ",";
    }
    std::cout << "\n";
    std::cout << "Tuple size (fixed): " << schema.TupleSize() << "\n";

    Tuple t(schema, {Value{int32_t{42}}, Value{3.14}, Value{std::string{"Alice"}}});

    Value vid    = t.GetValue(schema, 0);
    Value vscore = t.GetValue(schema, 1);
    Value vname  = t.GetValue(schema, 2);

    std::cout << "id=" << vid.ToString() << "\n";
    std::cout << "score=" << vscore.ToString() << "\n";
    std::cout << "name=" << vname.ToString() << "\n";
    std::cout << "Row: " << vid.ToString() << " | "
              << vscore.ToString() << " | " << vname.ToString() << "\n";

    return 0;
}
