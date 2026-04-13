# Smart Pointers and RAII

## Your Task

Implement three classes that demonstrate the ownership and lifetime patterns used throughout a real database storage engine.

### 1. `FileHandle`

A RAII wrapper around a POSIX file descriptor.

- Constructor: open the file with `open(path, O_RDWR | O_CREAT, 0644)`. Print `"FileHandle opened fd=<n>"`.
- Destructor: close the fd. Print `"FileHandle closed fd=<n>"`.
- Non-copyable, non-movable (database file handles are singletons per process).
- Expose `int Fd() const`.

### 2. `Page` and `PageGuard`

```cpp
struct Page {
    int page_id;
    bool is_pinned{true};
    std::array<std::byte, 64> data{};  // trimmed for demo
};
```

A `PageGuard` wraps a `std::unique_ptr<Page, PageDeleter>` where `PageDeleter` is a custom deleter struct. When the deleter fires it must:
1. Set `page->is_pinned = false`.
2. Print `"PageGuard released page <id>"`.

Provide:
- `PageGuard(Page* p)` — takes ownership.
- `Page* Get()` — raw pointer access.
- The guard must be movable but not copyable.

### 3. `Frame`

A reference-counted frame that wraps a `Page*` (non-owning pointer — the buffer pool owns the page array).

```cpp
class Frame {
public:
    explicit Frame(Page* p);
    Page* Get() const;
    long UseCount() const;   // delegates to shared_ptr use_count()
};
```

Print `"Frame destroyed for page <id>"` in the destructor of the internal control block (use a custom deleter on the `shared_ptr` — the deleter receives the `Page*` but does **not** delete it; it just prints).

## What to Print

```
FileHandle opened fd=3
Frame ref count: 1
Frame ref count: 2
Frame ref count: 1
Frame destroyed for page 0
PageGuard released page 0
FileHandle closed fd=3
```

(The exact fd number depends on the OS; `3` is typical when no other fds are open. Your output must match structurally — the fd value is acceptable to vary.)

## Constraints

- Compile with `g++ -std=c++20 -Wall -Wextra`.
- No memory leaks (valgrind-clean).
- Use `/tmp/db_raii_test.db` as the file path in `main`.
