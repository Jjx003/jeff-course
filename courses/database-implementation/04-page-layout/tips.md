# Tips & Notes

## Reading/writing header fields with memcpy

Direct pointer casts to `uint16_t*` inside a `std::array<std::byte>` are undefined behaviour (strict-aliasing violation). Use `memcpy` instead — the compiler will optimise it away:

```cpp
uint16_t GetNumSlots() const {
    uint16_t n;
    std::memcpy(&n, data_.data(), sizeof(n));
    return n;
}

void SetNumSlots(uint16_t n) {
    std::memcpy(data_.data(), &n, sizeof(n));
}
```

Or use `std::bit_cast` on a subarray if you prefer zero-copy reads.

## Slot array layout

Slot `i` lives at byte offset `4 + i * 4`. Each slot has two `uint16_t` fields: offset then length.

```cpp
struct Slot { uint16_t offset; uint16_t length; };

Slot GetSlot(uint16_t i) const {
    Slot s;
    std::memcpy(&s, data_.data() + 4 + i * 4, sizeof(Slot));
    return s;
}

void SetSlot(uint16_t i, Slot s) {
    std::memcpy(data_.data() + 4 + i * 4, &s, sizeof(Slot));
}
```

## InsertTuple step by step

1. Check `FreeSpace() >= 4 + len`. Return -1 if not.
2. Decrement `free_space_offset` by `len`. New tuple goes at `[free_space_offset, free_space_offset + len)`.
3. Copy `data` into `data_` at `free_space_offset`.
4. Write slot `{free_space_offset, len}` at index `num_slots`.
5. Increment `num_slots`.
6. Return the old `num_slots` (now the new slot's id).

## FreeSpace arithmetic

```
FreeSpace = free_space_offset - (4 + num_slots * 4)
```

This is the gap between where the next slot entry would go and where the next tuple would end.

## std::span return for GetTuple

```cpp
std::span<const std::byte> GetTuple(uint16_t slot_id) const {
    if (slot_id >= GetNumSlots()) return {};
    Slot s = GetSlot(slot_id);
    if (s.length == 0) return {};   // tombstone
    return {data_.data() + s.offset, s.length};
}
```

## Printing span as string

```cpp
auto sp = page.GetTuple(0);
std::string str(reinterpret_cast<const char*>(sp.data()), sp.size());
std::cout << str << "\n";
```
