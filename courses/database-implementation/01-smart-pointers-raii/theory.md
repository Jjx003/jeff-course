# Theory: Smart Pointers and RAII

## Why Ownership Matters in a Database

A database process juggles thousands of live objects — open file descriptors, pinned buffer frames, active transactions, index nodes — and must release every one of them exactly once, even when a query aborts mid-execution. Ownership bugs (double-free, leak, use-after-free) corrupt the on-disk format or crash the server under load. C++ gives you a zero-overhead way to make ownership explicit and automatic: **RAII**.

---

## RAII (Resource Acquisition Is Initialisation)

The invariant: a resource is acquired in a constructor and released in the corresponding destructor. Because C++ guarantees destructor calls on scope exit (including exception unwind), RAII makes leaks structurally impossible.

```cpp
FileHandle fh("/tmp/test.db");   // fd opened
{
    doWork(fh);
    // ... exception thrown here ...
}
// fh destructor runs regardless → fd closed
```

**Rule of Five.** If a class manages a resource, you must explicitly define (or delete) all five special members: destructor, copy constructor, copy assignment, move constructor, move assignment. Omitting any one lets the compiler generate a shallow copy that duplicates the resource handle without duplicating the resource — a recipe for double-free.

---

## `unique_ptr` with Custom Deleters

`std::unique_ptr<T, D>` accepts a second template parameter `D` for the deleter. This is how a `PageGuard` can "unpin" a page instead of `delete`-ing it:

```cpp
struct PageDeleter {
    void operator()(Page* p) const {
        p->is_pinned = false;
        // notify buffer pool, etc.
    }
};
using PageGuard = std::unique_ptr<Page, PageDeleter>;
```

The deleter is stored inside the `unique_ptr` (in an empty-base-optimization slot when it is a stateless struct), so there is no extra heap allocation. This is the pattern BusTub and CMU's DB courses use for their `BasicPageGuard`.

---

## `shared_ptr` and Reference Counting

`std::shared_ptr<T>` maintains an atomic reference count in a control block allocated on the heap. Every copy increments the count; every destruction decrements it. When the count reaches zero the deleter fires.

- **Overhead:** one heap allocation for the control block (avoided with `make_shared`), two words of storage (pointer + control block pointer), atomic increments.
- **Use in DBs:** buffer frames that are shared across multiple operators in the same query. The frame stays pinned as long as any executor holds a `shared_ptr` to it.
- **Cycle hazard:** `shared_ptr` cycles leak. Break cycles with `std::weak_ptr` — a non-owning observer that can be promoted to `shared_ptr` if the object is still alive.

---

## Database Context

| Resource | Typical wrapper | Why not raw pointer |
|----------|----------------|---------------------|
| File descriptor | `FileHandle` (RAII) | `close` must always run |
| Buffer frame | `PageGuard` (`unique_ptr` + deleter) | Unpin must run on scope exit |
| Shared frame | `Frame` (`shared_ptr`) | Multiple operators read same frame |
| Transaction | `Transaction` (RAII) | Abort must run on exception |

Every layer of the storage engine you build in this course will rely on one of these three patterns. Getting them right here means you won't debug lifetime bugs later.
