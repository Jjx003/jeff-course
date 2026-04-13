# Theory: Move Semantics and Templates

## Value Categories

Every C++ expression has a value category. The ones you care about:

- **lvalue** — has a name; can take its address. `Buffer<int> b(4); b` is an lvalue.
- **rvalue** — temporary or explicitly cast with `std::move`. `Buffer<int>(4)` is an rvalue.
- **xvalue** — "expiring value"; result of `std::move(b)`. The compiler is permitted to steal its resources.

`std::move` is a cast to `T&&`; it does not move anything. The actual resource transfer happens in the **move constructor** or **move assignment operator** you write.

---

## The Move Constructor Pattern

```cpp
Buffer(Buffer&& other) noexcept
    : data_(other.data_), size_(other.size_), cap_(other.cap_) {
    other.data_ = nullptr;
    other.size_ = 0;
    other.cap_  = 0;
}
```

The three-step: **steal**, **zero**. After the move, `other` must be in a valid but unspecified state. For a buffer, "valid but unspecified" means `nullptr`/0 — the destructor must be safe to call.

`noexcept` matters: the STL will use the move constructor instead of the copy constructor during reallocation (e.g., `std::vector` growth) **only** if the move constructor is marked `noexcept`. For DB engine buffers that hold page data, this avoids an unnecessary copy.

---

## `std::forward` and Perfect Forwarding

When writing a function template that forwards arguments to another function, use `std::forward<T>(arg)` to preserve the value category:

```cpp
template<typename T>
void emplace(T&& val) {
    new(slot_) T(std::forward<T>(val));  // move if rvalue, copy if lvalue
}
```

Without `std::forward`, `val` is always treated as an lvalue (it has a name), and you always copy — defeating the purpose.

---

## `if constexpr`

Introduced in C++17, `if constexpr` evaluates a constant expression at compile time and discards the untaken branch **entirely** — the discarded branch is not instantiated.

```cpp
template<typename T>
std::string describe(const T& val) {
    if constexpr (std::is_arithmetic_v<T>) {
        return std::to_string(val);   // only compiled for arithmetic T
    } else {
        return "<non-arithmetic>";
    }
}
```

This is cleaner than SFINAE (`std::enable_if`) or explicit template specialisation for straightforward compile-time branching. Use SFINAE when you need to participate in overload resolution; use `if constexpr` when you just need to branch on a type trait inside one function.

---

## Ring Buffers in Database Systems

A ring buffer (circular queue) is the standard data structure for:
- **WAL (Write-Ahead Log) buffers:** log records are appended at the tail; the flusher drains from the head.
- **Network send buffers:** pages serialized for wire transfer.
- **Producer–consumer queues between threads** in a parallel query executor.

`std::array<T, N>` gives stack allocation with known size — appropriate when `N` is a compile-time constant (e.g., `LOG_BUFFER_PAGES = 256`). Indices modulo `N` give the circular wrap.

---

## Why Copy-Delete a Buffer?

Copying a large buffer (multiple 4 KB pages) is expensive and almost never what you want. Explicit `= delete` on copy members forces the caller to be intentional: either move (cheap) or explicitly clone via a named `clone()` method. This is the same philosophy as `std::unique_ptr`.
