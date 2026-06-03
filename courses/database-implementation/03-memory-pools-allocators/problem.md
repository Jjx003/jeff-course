# Memory Pools and Allocators

## Your Task

### 1. `SlabAllocator<T, PoolSize>`

Pre-allocates a pool of exactly `PoolSize` objects of type `T` and manages them via a free-list. No calls to `new`/`delete` after construction.

```cpp
template<typename T, size_t PoolSize>
class SlabAllocator {
public:
    SlabAllocator();         // pre-allocate pool, build free list
    ~SlabAllocator();        // free the pool

    T* allocate();           // pop from free list; return nullptr if exhausted
    void deallocate(T* ptr); // push back onto free list

    size_t available() const; // slots remaining
};
```

Implementation requirements:
- Use `operator new` (or `std::aligned_alloc`) to allocate `PoolSize * sizeof(T)` bytes with alignment `alignof(T)`.
- Use a **free-list of `void*`**: store the next-pointer inside the free slot itself (the slot is large enough because `sizeof(T) >= sizeof(void*)` — you can static_assert this).
- `allocate()` must use **placement new** (`new(ptr) T()`) to construct the object.
- `deallocate(ptr)` must call `ptr->~T()` explicitly, then return the slot to the free list.
- Print `"Allocated @ 0x<hex>"` and `"Deallocated @ 0x<hex>"` for each call.

### 2. `PoolResource` — `std::pmr::memory_resource` wrapper

```cpp
class PoolResource : public std::pmr::memory_resource {
protected:
    void* do_allocate(size_t bytes, size_t alignment) override;
    void  do_deallocate(void* ptr, size_t bytes, size_t alignment) override;
    bool  do_is_equal(const std::pmr::memory_resource& other) const noexcept override;
};
```

Back `PoolResource` with a `SlabAllocator<std::byte, 1024>` (pool of raw bytes). `do_allocate` checks that `bytes <= sizeof(std::byte)` … actually since the pool holds `std::byte`-sized slots, make the pool hold **64-byte blocks** instead: use `std::aligned_storage_t<64, 64>` as the element type, and static_assert `bytes <= 64`.

Then use `PoolResource` with a `std::pmr::vector<int>`:

```cpp
PoolResource pool;
std::pmr::vector<int> v{&pool};
v.push_back(1); v.push_back(2); v.push_back(3);
```

## What to Print

```
Allocated @ 0x<addr0>
Allocated @ 0x<addr1>
Allocated @ 0x<addr2>
Allocated @ 0x<addr3>
Deallocated @ 0x<addr1>
Deallocated @ 0x<addr2>
Allocated @ 0x<addr2>
Allocated @ 0x<addr1>
Addresses reused: yes
pmr::vector values: 1 2 3
```

The free list is LIFO, so the most recently freed slot (`addr2`) is handed
back first, then `addr1`.

Because the printed hex addresses depend on where the OS places the pool, the
output is **not deterministic** and is not auto-graded against a fixed
reference. The key requirement is that the two re-allocated addresses match two
of the first four — demonstrating free-list reuse.

## Constraints

- Compile with `g++ -std=c++17 -Wall -Wextra`.
- No calls to `malloc`/`free`/`new`/`delete` after `SlabAllocator` construction.
- `static_assert(sizeof(T) >= sizeof(void*))` inside `SlabAllocator`.
