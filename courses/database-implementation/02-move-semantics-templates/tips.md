# Tips & Notes

## Move assignment must handle self-assignment

```cpp
Buffer& operator=(Buffer&& other) noexcept {
    if (this == &other) return *this;   // guard
    delete[] data_;                      // free current resource
    data_ = other.data_;
    size_ = other.size_;
    cap_  = other.cap_;
    other.data_ = nullptr;
    other.size_ = 0;
    other.cap_  = 0;
    return *this;
}
```

Omitting the self-assignment guard causes `delete[] data_` to free the memory you are about to steal — a hard-to-debug corruption.

## Ring buffer index arithmetic

Use two indices (`head_`, `tail_`) and a count:

```cpp
size_t head_{0}, tail_{0}, count_{0};

bool push(const T& val) {
    if (count_ == N) return false;
    data_[tail_] = val;
    tail_ = (tail_ + 1) % N;
    ++count_;
    return true;
}

bool pop(T& out) {
    if (count_ == 0) return false;
    out = data_[head_];
    head_ = (head_ + 1) % N;
    --count_;
    return true;
}
```

Never use `head_ == tail_` to distinguish empty vs. full — it is ambiguous. The separate `count_` is the simplest fix.

## `if constexpr` vs. `std::enable_if`

Both achieve compile-time branching, but they have different purposes:

| Technique | Use when |
|-----------|----------|
| `if constexpr` | Single function body, branch inside the body |
| `std::enable_if` | Need different overloads to participate in overload resolution |
| Template specialisation | Need fundamentally different implementations per type |

For `to_string_if_arithmetic`, `if constexpr` is the right tool — one function, two branches.

## Verifying the move left the source empty

After `Buffer<int> dst(std::move(src))`:
- `src.Data()` must be `nullptr`
- `src.Size()` must be `0`

Test this in `main` with an `assert` or a print-and-compare — the grader will check the printed output.

## `noexcept` on move members

Always mark move constructor and move assignment `noexcept` when possible. The STL containers check `std::is_nothrow_move_constructible` at compile time and fall back to copy if the move can throw. A buffer that copies when it should move is a performance bug, not a correctness bug — but in a high-throughput storage engine, those add up.
