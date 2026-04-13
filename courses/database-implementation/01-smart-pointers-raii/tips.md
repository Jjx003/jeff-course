# Tips & Notes

## Rule of Five checklist

For any resource-owning class, explicitly handle all five:

```cpp
class FileHandle {
public:
    FileHandle(const char* path);        // acquire
    ~FileHandle();                        // release
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;
    FileHandle(FileHandle&&) = delete;   // single-owner: no move either
    FileHandle& operator=(FileHandle&&) = delete;
};
```

If you omit `= delete` on the copy members, the compiler generates a shallow copy that duplicates the `int fd_` — you'll close the same fd twice.

## Custom deleter as a struct vs. lambda

A lambda deleter works but inflates the `unique_ptr` size if it captures state:

```cpp
// Stateless struct — zero overhead (empty-base opt.)
struct PageDeleter { void operator()(Page* p) const { /* ... */ } };
std::unique_ptr<Page, PageDeleter> guard(page_ptr);

// Lambda — also zero overhead only if captureless
auto del = [](Page* p){ /* ... */ };
std::unique_ptr<Page, decltype(del)> guard(page_ptr, del);
```

Use a named struct when the deleter needs to appear in a type alias or across translation units.

## `shared_ptr` custom deleter for non-delete actions

```cpp
auto frame_ptr = std::shared_ptr<Page>(raw_page,
    [](Page* p){ std::cout << "Frame destroyed for page " << p->page_id << "\n"; }
    // does NOT call delete — the buffer pool owns the array
);
```

The deleter receives the managed pointer but ownership of the storage lives elsewhere. This is how the buffer pool can hand out `shared_ptr<Page>` without losing control of the underlying `Page` array.

## Checking fd validity

`open()` returns `-1` on failure and sets `errno`. Always check:

```cpp
fd_ = open(path, O_RDWR | O_CREAT, 0644);
if (fd_ < 0) throw std::system_error(errno, std::system_category());
```

## Order of destruction in `main`

C++ destroys local variables in **reverse declaration order**. If you want the `PageGuard` destroyed before `FileHandle`, declare `FileHandle` first. This is the same ordering guarantee you rely on when stacking RAII objects in a real storage engine initialization sequence.
