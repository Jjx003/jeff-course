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
        fd_ = open(path, O_RDWR | O_CREAT, 0644);
        if (fd_ < 0) {
            throw std::system_error(errno, std::system_category(),
                                    "FileHandle: open failed");
        }
        std::cout << "FileHandle opened fd=" << fd_ << "\n";
    }

    ~FileHandle() {
        if (fd_ >= 0) {
            std::cout << "FileHandle closed fd=" << fd_ << "\n";
            close(fd_);
        }
    }

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

struct PageDeleter {
    void operator()(Page* p) const {
        p->is_pinned = false;
        std::cout << "PageGuard released page " << p->page_id << "\n";
    }
};

class PageGuard {
public:
    explicit PageGuard(Page* p) : ptr_(p, PageDeleter{}) {}

    Page* Get() const { return ptr_.get(); }

    PageGuard(PageGuard&&) = default;
    PageGuard& operator=(PageGuard&&) = default;
    PageGuard(const PageGuard&) = delete;
    PageGuard& operator=(const PageGuard&) = delete;

private:
    std::unique_ptr<Page, PageDeleter> ptr_;
};

// ---------------------------------------------------------------------------
// Part 3: Frame — shared_ptr-based reference-counted wrapper
// ---------------------------------------------------------------------------

class Frame {
public:
    explicit Frame(Page* p)
        : ptr_(p, [](Page* pg) {
              std::cout << "Frame destroyed for page " << pg->page_id << "\n";
              // Does NOT delete — the buffer pool owns the array
          }) {}

    Page* Get() const { return ptr_.get(); }
    long UseCount() const { return ptr_.use_count(); }

private:
    std::shared_ptr<Page> ptr_;
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    FileHandle fh("/tmp/db_raii_test.db");

    Page page;
    page.page_id = 0;

    {
        Frame f1(&page);
        std::cout << "Frame ref count: " << f1.UseCount() << "\n";  // 1
        {
            Frame f2 = f1;
            std::cout << "Frame ref count: " << f1.UseCount() << "\n";  // 2
        }
        std::cout << "Frame ref count: " << f1.UseCount() << "\n";  // 1
    }
    // "Frame destroyed for page 0"

    {
        PageGuard guard(&page);
    }
    // "PageGuard released page 0"

    // "FileHandle closed fd=3"
    return 0;
}
