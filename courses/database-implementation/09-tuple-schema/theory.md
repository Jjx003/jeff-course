# Theory: Tuple and Schema

## Why a Typed Schema?

A database table stores heterogeneous data — integers, floats, strings — in a uniform byte sequence. The schema is the **blueprint** that tells the executor how to interpret those bytes. Without a schema, a sequence of bytes is meaningless. With a schema, the executor knows: "bytes 0–3 are a 4-byte little-endian int; bytes 4–11 are a double; bytes 12–15 are a 4-byte length prefix for a variable-length string starting at byte 16."

---

## Fixed-Size vs. Variable-Length Fields

**Fixed-size fields** (INT32, INT64, FLOAT64): stored at a known offset. `GetValue` for column $i$ is a single `memcpy` at `offset_i`. No scanning required.

**Variable-length fields** (VARCHAR): the fixed-size region stores a compact representation (length prefix + offset into a variable section, or an inline buffer). The actual string may be in:
- An inline buffer in the tuple (simple, but wastes space for short strings).
- An overflow page referenced by a pointer (used by PostgreSQL for long strings — `TOAST`).

For this module, VARCHAR is simplified: fixed region holds a `uint32_t` offset into a variable section appended to the tuple's byte array.

---

## `std::variant` for Union Types

`std::variant<T1, T2, ...>` is a type-safe tagged union. Unlike C `union`, it knows which alternative is active and calls the correct destructor:

```cpp
std::variant<int32_t, double, std::string> v = std::string("hello");
std::get<std::string>(v);          // "hello"
std::get_if<int32_t>(&v);          // nullptr — wrong type
std::holds_alternative<std::string>(v);  // true
```

`std::visit` applies a callable to the active alternative — useful for `ToString()`:

```cpp
std::string ToString() const {
    return std::visit([](auto&& val) -> std::string {
        using T = std::decay_t<decltype(val)>;
        if constexpr (std::is_same_v<T, std::string>) return val;
        else return std::to_string(val);
    }, data_);
}
```

---

## Offset-Based Layout

Given a schema with columns of sizes $s_0, s_1, \dots, s_{n-1}$, the offset of column $i$ is:

$$\text{offset}_i = \sum_{j=0}^{i-1} s_j$$

The total fixed-size region is $\sum_j s_j$. This layout is identical to a C `struct` with no padding (though you may need `#pragma pack` or explicit padding to match C ABI).

---

## Why Not Use `std::any`?

`std::any` is type-erased and requires RTTI for type-safe access. `std::variant` is:
- Faster: no heap allocation for small types.
- Statically checked: `std::get<T>` throws at runtime for wrong type; `std::visit` forces you to handle all alternatives.
- Inspectable: `std::variant_size_v` and `std::variant_alternative_t` enable compile-time reflection.

For a system with a fixed, known set of SQL types, `std::variant` is the right tool.

---

## Database Context

The `Value` and `Tuple` classes you implement here are used by every operator:
- `SeqScanExecutor` calls `GetValue` on each tuple to evaluate a predicate.
- `HashJoinExecutor` calls `GetValue` to extract join keys.
- `ProjectExecutor` calls `GetValue` on selected columns and assembles a new tuple.

Getting the layout right now prevents subtle offset bugs in every downstream module.
