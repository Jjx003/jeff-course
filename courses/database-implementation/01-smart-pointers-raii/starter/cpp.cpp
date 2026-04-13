#include <array>
#include <cstddef>
#include <fcntl.h>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <system_error>
#include <unistd.h>

// ---------------------------------------------------------------------------
// Part 1: FileHandle — RAII wrapper around a POSIX file descriptor
// ---------------------------------------------------------------------------

class FileHandle {
public:
    explicit FileHandle(const char* path) {
        // TODO: open the file with O_RDWR | O_CREAT, mode 0644
        //       store the fd in fd_
        //       throw std::system_error if open() returns -1
        //       print "FileHandle opened fd=<n>"
    }

    ~FileHandle() {
        // TODO: close fd_ and print "FileHandle closed fd=<n>"
    }

    // Non-copyable, non-movable
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;
    FileHandle(FileHandle&&) = delete;
    FileHandle& operator=(FileHandle&&) = delete;

    int Fd() const { return fd_; }

private:
    int fd_{-1};
};

// ---------------------------------------------------------------------------
// Part 2: Page and PageGuard
// ---------------------------------------------------------------------------

struct Page {
    int page_id{0};
    bool is_pinned{true};
    std::array<std::byte, 64> data{};
};

// TODO: define PageDeleter — a struct with operator()(Page*) that:
//       1. sets page->is_pinned = false
//       2. prints "PageGuard released page <id>"

struct PageDeleter {
    void operator()(Page* p) const {
        // TODO
    }
};

// PageGuard: unique_ptr<Page, PageDeleter>
// TODO: define the type alias and provide:
//       PageGuard(Page* p)  — takes ownership
//       Page* Get()         — raw pointer access
// Hint: you can wrap unique_ptr<Page,PageDeleter> in a class OR
//       simply make a type alias and construct directly in main.

class PageGuard {
public:
    explicit PageGuard(Page* p) {
        // TODO: store p in a unique_ptr<Page, PageDeleter>
    }

    Page* Get() const {
        // TODO: return raw pointer
        return nullptr;
    }

    // movable, not copyable
    PageGuard(PageGuard&&) = default;
    PageGuard& operator=(PageGuard&&) = default;
    PageGuard(const PageGuard&) = delete;
    PageGuard& operator=(const PageGuard&) = delete;

private:
    // TODO: member unique_ptr<Page, PageDeleter>
};

// ---------------------------------------------------------------------------
// Part 3: Frame — shared_ptr-based reference-counted wrapper
// ---------------------------------------------------------------------------

class Frame {
public:
    // TODO: constructor takes Page* (non-owning)
    //       create a shared_ptr with a custom deleter that prints
    //       "Frame destroyed for page <id>" but does NOT delete the page
    explicit Frame(Page* p) {
        // TODO
    }

    Page* Get() const {
        // TODO
        return nullptr;
    }

    long UseCount() const {
        // TODO: return shared_ptr use_count()
        return 0;
    }

private:
    // TODO: std::shared_ptr<Page> member
};

// ---------------------------------------------------------------------------
// main — exercises all three classes
// ---------------------------------------------------------------------------

int main() {
    // 1. Open a file handle
    FileHandle fh("/tmp/db_raii_test.db");

    // 2. Create a Page on the heap (simulating buffer pool memory)
    Page page;
    page.page_id = 0;

    // 3. Demonstrate Frame reference counting
    {
        Frame f1(&page);
        std::cout << "Frame ref count: " << f1.UseCount() << "\n";  // 1
        {
            Frame f2 = f1;   // TODO: Frame needs to be copyable (shared ownership)
            std::cout << "Frame ref count: " << f1.UseCount() << "\n";  // 2
        }
        std::cout << "Frame ref count: " << f1.UseCount() << "\n";  // 1
    }
    // Frame destroyed here → prints "Frame destroyed for page 0"

    // 4. Demonstrate PageGuard
    {
        PageGuard guard(&page);
        // guard goes out of scope → PageDeleter fires
    }
    // prints "PageGuard released page 0"

    // fh goes out of scope last → "FileHandle closed fd=<n>"
    return 0;
}
