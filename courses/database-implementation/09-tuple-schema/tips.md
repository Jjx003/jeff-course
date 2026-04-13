# Tips & Notes

## Computing column offsets in Schema constructor

```cpp
size_t offset = 0;
for (auto& [name, type] : cols) {
    size_t sz = TypeSize(type);
    columns_.push_back({name, type, offset, sz});
    offset += sz;
}
tuple_size_ = offset;
```

Where:
```cpp
static size_t TypeSize(TypeId t) {
    switch (t) {
        case TypeId::INT32:   return 4;
        case TypeId::INT64:   return 8;
        case TypeId::FLOAT64: return 8;
        case TypeId::VARCHAR: return 4;  // length prefix
    }
    return 0;
}
```

## Storing a Tuple from Values

```cpp
Tuple::Tuple(const Schema& schema, std::initializer_list<Value> values) {
    // Allocate fixed-size region
    data_.resize(schema.TupleSize());
    size_t i = 0;
    for (const Value& v : values) {
        const Column& col = schema.GetColumn(i++);
        if (col.type == TypeId::INT32) {
            int32_t x = v.AsInt32();
            std::memcpy(data_.data() + col.offset, &x, 4);
        } else if (col.type == TypeId::FLOAT64) {
            double x = v.AsFloat64();
            std::memcpy(data_.data() + col.offset, &x, 8);
        } else if (col.type == TypeId::VARCHAR) {
            // Append string to variable-length section
            uint32_t var_offset = static_cast<uint32_t>(data_.size() - schema.TupleSize());
            std::memcpy(data_.data() + col.offset, &var_offset, 4);
            const std::string& s = v.AsVarchar();
            for (char c : s) data_.push_back(static_cast<std::byte>(c));
            data_.push_back(std::byte{0});  // null terminator
        }
        // ... INT64 similarly
    }
}
```

## Extracting a VARCHAR in GetValue

```cpp
uint32_t var_offset;
std::memcpy(&var_offset, data_.data() + col.offset, 4);
const char* str = reinterpret_cast<const char*>(
    data_.data() + schema.TupleSize() + var_offset);
return Value{std::string(str)};
```

## std::visit for ToString

```cpp
std::string ToString() const {
    return std::visit([](auto&& v) -> std::string {
        using T = std::decay_t<decltype(v)>;
        if constexpr (std::is_same_v<T, std::string>) return v;
        else return std::to_string(v);
    }, data_);
}
```

## Printing a row

```cpp
for (size_t i = 0; i < schema.NumColumns(); ++i) {
    if (i > 0) std::cout << " | ";
    std::cout << tuple.GetValue(schema, i).ToString();
}
std::cout << "\n";
```
