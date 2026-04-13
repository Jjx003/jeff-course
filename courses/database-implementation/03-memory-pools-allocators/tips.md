# Tips & Notes

## Building the free list in the constructor

Initialize the entire pool as a chain:

```cpp
SlabAllocator() {
    pool_ = static_cast<T*>(::operator new(PoolSize * sizeof(T),
                                           std::align_val_t{alignof(T)}));
    // Link slots together
    for (size_t i = 0; i < PoolSize - 1; ++i) {
        void* slot = static_cast<void*>(pool_ + i);
        *reinterpret_cast<void**>(slot) = static_cast<void*>(pool_ + i + 1);
    }
    // Last slot points to nullptr
    *reinterpret_cast<void**>(pool_ + PoolSize - 1) = nullptr;
    free_list_ = static_cast<void*>(pool_);
}
```

## Placement new requires `<new>`

```cpp
#include <new>   // for placement new and std::align_val_t
```

Without this header, placement new may not compile on some toolchains.

## `do_is_equal` for pmr

The simplest correct implementation:

```cpp
bool do_is_equal(const std::pmr::memory_resource& other) const noexcept override {
    return this == &other;
}
```

Two `PoolResource` instances are not interchangeable — memory from one cannot be freed by the other.

## pmr::vector allocation size

`std::pmr::vector<int>` may request a block larger than `sizeof(int)` on `push_back` due to capacity doubling. If your pool blocks are 64 bytes, a vector of 3 ints (12 bytes) fits in one block. For production use you would need a more flexible backing store; for this exercise, 64 bytes per allocation is sufficient.

## Printing addresses

```cpp
std::cout << "Allocated @ " << static_cast<void*>(ptr) << "\n";
```

`std::cout` with `void*` prints the pointer in implementation-defined format (hex on most platforms). For consistent hex output:

```cpp
std::cout << "Allocated @ 0x" << std::hex << reinterpret_cast<uintptr_t>(ptr) << std::dec << "\n";
```

## Verifying reuse

Store the first four addresses in a `std::array<void*, 4>`. After deallocating indices 1 and 2 and re-allocating, check that the new addresses appear in the saved array. The free list is LIFO, so the last-deallocated slot is the first re-allocated.
