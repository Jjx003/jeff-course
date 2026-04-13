# Move Semantics and Templates

## Your Task

### 1. `Buffer<T>`

A heap-owning buffer — copy-deleted, move-only.

```cpp
template<typename T>
class Buffer {
public:
    Buffer(size_t size);               // allocate size * sizeof(T) bytes
    ~Buffer();                          // free allocation

    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;

    Buffer(Buffer&& other) noexcept;           // steal data_/size_/cap_; zero out source
    Buffer& operator=(Buffer&& other) noexcept;

    T*     Data() const { return data_; }
    size_t Size() const { return size_; }

private:
    T*     data_{nullptr};
    size_t size_{0};
    size_t cap_{0};
};
```

Requirements:
- After a move, the source's `Data()` must return `nullptr` and `Size()` must return `0`.
- Print `"Buffer moved: source size=0"` at the end of each move constructor/assignment (after zeroing the source).

### 2. `RingBuffer<T, N>`

Fixed-capacity circular queue backed by a `std::array<T, N>`.

```cpp
template<typename T, size_t N>
class RingBuffer {
public:
    bool push(const T& val);   // false if full
    bool pop(T& out);          // false if empty
    bool empty() const;
    bool full()  const;
    size_t size() const;
};
```

### 3. `to_string` via `if constexpr`

Add a free function template:

```cpp
template<typename T>
std::string to_string_if_arithmetic(const T& val);
```

- If `T` satisfies `std::is_arithmetic_v<T>`, return `std::to_string(val)`.
- Otherwise, return `"<non-arithmetic>"`.
- Use `if constexpr`, not SFINAE or specialisation.

## What to Print

```
Buffer<int> size=4
Buffer moved: source size=0
After move: src.Size()=0 dst.Size()=4

RingBuffer push: 10 20 30
RingBuffer pop: 10
RingBuffer size: 2

to_string(42): 42
to_string(3.14): 3.140000
to_string(string): <non-arithmetic>
```

## Constraints

- Compile with `g++ -std=c++20 -Wall -Wextra`.
- `Buffer` must pass a move-safety check: verifying the moved-from object has `nullptr`/0.
