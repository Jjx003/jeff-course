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
    switch (t) {
        case TypeId::INT32:   return 4;
        case TypeId::INT64:   return 8;
        case TypeId::FLOAT64: return 8;
        case TypeId::VARCHAR: return 4;
    }
    return 0;
}

static std::string TypeName(TypeId t) {
    switch (t) {
        case TypeId::INT32:   return "INT32";
        case TypeId::INT64:   return "INT64";
        case TypeId::FLOAT64: return "FLOAT64";
        case TypeId::VARCHAR: return "VARCHAR";
    }
    return "UNKNOWN";
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
    Schema(std::initializer_list<std::pair<std::string, TypeId>> cols) {
        size_t offset = 0;
        for (auto& [name, type] : cols) {
            size_t sz = TypeSize(type);
            columns_.push_back({name, type, offset, sz});
            offset += sz;
        }
        tuple_size_ = offset;
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

// ---------------------------------------------------------------------------
// Tuple
// ---------------------------------------------------------------------------

class Tuple {
public:
    Tuple() = default;

    Tuple(const Schema& schema, std::initializer_list<Value> values) {
        data_.resize(schema.TupleSize());
        size_t i = 0;
        for (const Value& v : values) {
            const Column& col = schema.GetColumn(i++);
            switch (col.type) {
                case TypeId::INT32: {
                    int32_t x = v.AsInt32();
                    std::memcpy(data_.data() + col.offset, &x, 4);
                    break;
                }
                case TypeId::INT64: {
                    int64_t x = v.AsInt64();
                    std::memcpy(data_.data() + col.offset, &x, 8);
                    break;
                }
                case TypeId::FLOAT64: {
                    double x = v.AsFloat64();
                    std::memcpy(data_.data() + col.offset, &x, 8);
                    break;
                }
                case TypeId::VARCHAR: {
                    uint32_t var_off = static_cast<uint32_t>(data_.size() - schema.TupleSize());
                    std::memcpy(data_.data() + col.offset, &var_off, 4);
                    const std::string& s = v.AsVarchar();
                    for (char c : s) data_.push_back(static_cast<std::byte>(c));
                    data_.push_back(std::byte{0});
                    break;
                }
            }
        }
    }

    Value GetValue(const Schema& schema, size_t col_idx) const {
        const Column& col = schema.GetColumn(col_idx);
        switch (col.type) {
            case TypeId::INT32: {
                int32_t x;
                std::memcpy(&x, data_.data() + col.offset, 4);
                return Value{x};
            }
            case TypeId::INT64: {
                int64_t x;
                std::memcpy(&x, data_.data() + col.offset, 8);
                return Value{x};
            }
            case TypeId::FLOAT64: {
                double x;
                std::memcpy(&x, data_.data() + col.offset, 8);
                return Value{x};
            }
            case TypeId::VARCHAR: {
                uint32_t var_off;
                std::memcpy(&var_off, data_.data() + col.offset, 4);
                const char* str = reinterpret_cast<const char*>(
                    data_.data() + schema.TupleSize() + var_off);
                return Value{std::string(str)};
            }
        }
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

    std::cout << "Schema:";
    for (size_t i = 0; i < schema.NumColumns(); ++i) {
        const Column& c = schema.GetColumn(i);
        std::cout << " " << c.name << " " << TypeName(c.type);
        if (i + 1 < schema.NumColumns()) std::cout << ",";
    }
    std::cout << "\n";
    std::cout << "Tuple size (fixed): " << schema.TupleSize() << "\n";

    Tuple t(schema, {Value{int32_t{42}}, Value{3.14}, Value{std::string{"Alice"}}});

    Value vid   = t.GetValue(schema, 0);
    Value vscore = t.GetValue(schema, 1);
    Value vname  = t.GetValue(schema, 2);

    std::cout << "id=" << vid.ToString() << "\n";
    std::cout << "score=" << vscore.ToString() << "\n";
    std::cout << "name=" << vname.ToString() << "\n";

    std::cout << "Row: " << vid.ToString() << " | " << vscore.ToString()
              << " | " << vname.ToString() << "\n";

    return 0;
}
