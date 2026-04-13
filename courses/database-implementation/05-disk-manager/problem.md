# Disk Manager

## Your Task

Implement `DiskManager` — the I/O layer for your database. It manages a single binary file and exposes page-granular read/write operations.

```cpp
using page_id_t = uint32_t;
constexpr size_t PAGE_SIZE = 4096;

class DiskManager {
public:
    explicit DiskManager(const std::string& db_file);
    ~DiskManager();

    // Extend the file by one page and return its id.
    page_id_t AllocatePage();

    // Write exactly PAGE_SIZE bytes from data to page id's file offset.
    void WritePage(page_id_t id, const std::byte* data);

    // Read exactly PAGE_SIZE bytes from page id's file offset into out.
    void ReadPage(page_id_t id, std::byte* out);

    page_id_t NumPages() const;
};
```

### File layout

Page `id` lives at byte offset `id * PAGE_SIZE`. The file is always an exact multiple of `PAGE_SIZE` in length.

### I/O primitives

Use `pwrite(fd, data, PAGE_SIZE, offset)` and `pread(fd, out, PAGE_SIZE, offset)`. Both are atomic with respect to the file position (unlike `write`/`read` which move the cursor), making them safe to call from multiple threads.

Check return values: `pwrite`/`pread` must return exactly `PAGE_SIZE` bytes, otherwise throw `std::runtime_error`.

### `AllocatePage`

Extend the file by `PAGE_SIZE` zero bytes and return the new page's id. Use `ftruncate(fd, new_size)` or write a zero-filled page.

## What to Print

```
Allocated page 0
Allocated page 1
Allocated page 2
Wrote page 0
Wrote page 1
Wrote page 2
Page 0: OK
Page 1: OK
Page 2: OK
```

Use `/tmp/test_disk.db` in `main`. Write a distinct repeating byte pattern per page (e.g., page 0 filled with `0xAA`, page 1 with `0xBB`, page 2 with `0xCC`) and verify the pattern round-trips correctly.

## Constraints

- Compile with `g++ -std=c++20 -Wall -Wextra`.
- Use `O_RDWR | O_CREAT | O_TRUNC` when opening the file.
- No `std::fstream` — use POSIX `open`/`pread`/`pwrite`/`close`.
