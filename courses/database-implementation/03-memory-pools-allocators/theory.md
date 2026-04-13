# Theory: Memory Pools and Allocators

## Why Custom Allocators in a Database

The system allocator (`malloc`) is general-purpose: it handles any size, any alignment, any threading pattern. That generality costs latency (~100 ns per call on a contentious heap) and cache locality. A database storage engine has a very different allocation profile:

- **Buffer pool frames** are all the same size (4 KB).
- **B+ tree nodes** are all the same size (one page).
- **Tuple descriptors** are small, short-lived, and allocated/freed in bursts during query execution.

For each of these, a **slab allocator** (also called a pool allocator) is strictly better: O(1) alloc/free with zero fragmentation for fixed-size objects.

---

## Placement New and Explicit Destructors

Normal `new T(args)` allocates memory **and** constructs. Placement new separates the two:

```cpp
void* slot = pool.get_slot();
T* obj = new(slot) T(args);   // construct in-place, no allocation
```

Because you bypassed `new`, you must also bypass `delete`. Call the destructor explicitly before returning the slot to the pool:

```cpp
obj->~T();                     // destruct, no deallocation
pool.return_slot(slot);
```

This is the only legal way to call a destructor directly. Calling it twice (e.g., via `delete`) is undefined behaviour.

---

## Free-List Implementation

Store the next-free pointer **inside** the free slot itself. Since the slot is at least `sizeof(void*)` bytes (enforced by `static_assert`), you can safely reinterpret:

```cpp
// On deallocate:
*reinterpret_cast<void**>(ptr) = free_list_;
free_list_ = ptr;

// On allocate:
void* slot = free_list_;
free_list_ = *reinterpret_cast<void**>(slot);
```

This gives O(1) push and pop with zero extra memory.

---

## `std::pmr` — Polymorphic Memory Resources

C++17's `<memory_resource>` provides a runtime-polymorphic allocator interface:

```
std::pmr::memory_resource (abstract)
  ├─ std::pmr::monotonic_buffer_resource   (bump allocator, no free)
  ├─ std::pmr::synchronized_pool_resource  (thread-safe pool)
  ├─ std::pmr::unsynchronized_pool_resource
  └─ your PoolResource
```

Any `std::pmr::` container (`vector`, `map`, `string`, …) takes a `memory_resource*` and forwards all allocations through it. This lets you swap allocators at runtime without changing container code — exactly the interface a database query executor needs to route allocations to the right pool per-query.

---

## Alignment

`alignof(T)` is the alignment requirement of type `T`. Misaligned access to `double` or SIMD types causes a bus error on strict-alignment architectures (ARM) or a performance penalty on x86. `std::aligned_alloc(alignment, size)` and `operator new(size, std::align_val_t{alignment})` guarantee alignment.

For a slab of same-type objects, allocating the entire slab with `alignof(T)` alignment ensures every slot is correctly aligned — because slots are `sizeof(T)` apart and `alignof(T)` divides `sizeof(T)`.

---

## Database Context

| Allocator type | DB use case |
|----------------|-------------|
| Slab / pool | B+ tree nodes, buffer frames, fixed-size log records |
| Monotonic (arena) | Query execution context: allocate freely, free all at once when the query finishes |
| pmr container | Executor-local `vector<Tuple>` backed by a per-query arena |

The CMU BusTub storage engine uses a similar `SlabAllocator` for its page table entries. PostgreSQL's `MemoryContext` is an arena allocator used throughout query execution.
