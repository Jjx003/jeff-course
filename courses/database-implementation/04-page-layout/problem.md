# Page Layout — Slotted Pages

## Your Task

Implement a 4096-byte `Page` class using a **slotted-page layout**.

### Layout

```
Offset 0         → [num_slots: uint16]
Offset 2         → [free_space_offset: uint16]   (starts at 4096)
Offset 4         → [slot 0: {offset: uint16, length: uint16}]
Offset 4+4*i     → [slot i: {offset: uint16, length: uint16}]
...                  (slot array grows downward toward tuples)
                 → [free space]
...
high addresses   → [tuple data packed from the end upward]
Offset 4096      → (one past end)
```

A **slot** is 4 bytes: `{uint16_t offset, uint16_t length}`. `length == 0` marks a deleted (tombstone) slot.

`GetTuple` returns a small non-owning view over the tuple's bytes. Since
`std::span` is a C++20 feature and this course compiles with `-std=c++17`,
define a minimal view yourself:

```cpp
struct ByteSpan {
    const std::byte* ptr{nullptr};
    size_t           len{0};
    const std::byte* data() const { return ptr; }
    size_t           size() const { return len; }
    bool             empty() const { return len == 0; }
};
```

### API

```cpp
class Page {
public:
    static constexpr size_t SIZE = 4096;

    Page();  // zero-initialise data_, set num_slots=0, free_space_offset=4096

    // Insert tuple. Returns slot_id (0-based) on success, -1 if no space.
    int InsertTuple(const std::byte* data, uint16_t len);

    // Return a view over tuple bytes. Empty view if slot is deleted or out of range.
    ByteSpan GetTuple(uint16_t slot_id) const;

    // Mark slot as deleted (set length=0). No-op if out of range.
    void DeleteTuple(uint16_t slot_id);

    // Available bytes for new data (accounts for slot entry + tuple bytes).
    uint16_t FreeSpace() const;

private:
    std::array<std::byte, SIZE> data_{};
};
```

### FreeSpace calculation

```
free = free_space_offset - (4 + num_slots * 4)
```

For an insert to succeed: `free >= 4 + len` (4 bytes for the new slot entry, `len` bytes for the tuple).

### What to print

Insert these three tuples:
- `"Hello"` (5 bytes)
- `"World!"` (6 bytes)
- `"DB"` (2 bytes)

Then:
1. Print each tuple's bytes as a string.
2. Delete slot 1.
3. Print free space before and after deletion.
4. Verify slot 1 returns an empty view after deletion.

```
Inserted slot 0: Hello
Inserted slot 1: World!
Inserted slot 2: DB
FreeSpace before delete: 4067
Deleted slot 1
FreeSpace after delete: 4067
GetTuple(1) after delete: <deleted>
GetTuple(0): Hello
GetTuple(2): DB
```

## Constraints

- Compile with `g++ -std=c++17 -Wall -Wextra`.
- `Page` must fit exactly in `std::array<std::byte, 4096>` — no extra heap allocation.
- Use `memcpy` for reading/writing multi-byte fields in `data_` (a direct
  reinterpret-cast to `uint16_t*` would violate strict aliasing).
