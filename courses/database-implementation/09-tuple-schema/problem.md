# Tuple and Schema

## Your Task

Implement the type system and tuple representation used by every operator in the query executor.

### `TypeId`

```cpp
enum class TypeId { INT32, INT64, FLOAT64, VARCHAR };
```

### `Column`

```cpp
struct Column {
    std::string name;
    TypeId      type;
    size_t      offset;   // byte offset within the tuple's fixed-size region
    size_t      size;     // size in bytes (4, 8, 8, or sizeof(uint32_t) for VARCHAR length prefix)
};
```

### `Schema`

```cpp
class Schema {
public:
    Schema(std::initializer_list<std::pair<std::string, TypeId>> cols);
    const Column& GetColumn(size_t idx) const;
    size_t        NumColumns() const;
    size_t        TupleSize() const;   // fixed-size region (excluding varchar data)
};
```

Column offsets are computed sequentially:
- `INT32`: 4 bytes
- `INT64`: 8 bytes
- `FLOAT64`: 8 bytes
- `VARCHAR`: 4 bytes for a `uint32_t` length prefix (the actual string is stored after the fixed region — you may simplify and store VARCHAR inline up to 32 bytes)

### `Value`

```cpp
class Value {
public:
    explicit Value(int32_t v);
    explicit Value(int64_t v);
    explicit Value(double v);
    explicit Value(std::string v);

    TypeId      Type() const;
    std::string ToString() const;

    // Typed accessors
    int32_t     AsInt32()   const;
    int64_t     AsInt64()   const;
    double      AsFloat64() const;
    std::string AsVarchar() const;
};
```

### `Tuple`

```cpp
class Tuple {
public:
    // Construct from a list of Values according to a Schema
    Tuple(const Schema& schema, std::initializer_list<Value> values);

    // Extract typed Value for column idx
    Value GetValue(const Schema& schema, size_t col_idx) const;

    const std::vector<std::byte>& Data() const;
};
```

For simplicity, store VARCHAR strings directly as a null-terminated sequence of bytes in a variable-length section appended after the fixed region. The fixed-region `uint32_t` for VARCHAR holds the offset into this variable-length section.

## What to Print

```
Schema: id INT32, score FLOAT64, name VARCHAR
Tuple size (fixed): 16
id=42
score=3.140000
name=Alice
Row: 42 | 3.140000 | Alice
```

## Constraints

- Compile with `g++ -std=c++17 -Wall -Wextra`.
- Use `std::variant<int32_t, int64_t, double, std::string>` for `Value`'s storage.
- `ToString()` on INT32/INT64 uses `std::to_string`; on FLOAT64 uses `std::to_string` (6 decimal places default); on VARCHAR returns the string directly.
