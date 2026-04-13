#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <iostream>
#include <stdexcept>
#include <string>
#include <system_error>
#include <unistd.h>

using page_id_t = uint32_t;
constexpr size_t PAGE_SIZE = 4096;

// ---------------------------------------------------------------------------
// DiskManager
// ---------------------------------------------------------------------------

class DiskManager {
public:
    explicit DiskManager(const std::string& db_file) {
        // TODO: open db_file with O_RDWR | O_CREAT | O_TRUNC, mode 0644
        //       throw std::system_error on failure
        //       initialise num_pages_ = 0
    }

    ~DiskManager() {
        // TODO: close fd_ if open
    }

    // Extend file by PAGE_SIZE and return new page id.
    page_id_t AllocatePage() {
        // TODO: page id = num_pages_++
        //       ftruncate to num_pages_ * PAGE_SIZE
        //       return page id
        return 0;
    }

    // Write PAGE_SIZE bytes from data to page id's offset.
    void WritePage(page_id_t id, const std::byte* data) {
        // TODO: compute offset = id * PAGE_SIZE
        //       pwrite(fd_, data, PAGE_SIZE, offset)
        //       check return == PAGE_SIZE
    }

    // Read PAGE_SIZE bytes from page id's offset into out.
    void ReadPage(page_id_t id, std::byte* out) {
        // TODO: compute offset = id * PAGE_SIZE
        //       pread(fd_, out, PAGE_SIZE, offset)
        //       check return == PAGE_SIZE
    }

    page_id_t NumPages() const { return num_pages_; }

private:
    int       fd_{-1};
    page_id_t num_pages_{0};
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    DiskManager dm("/tmp/test_disk.db");

    // Allocate 3 pages
    page_id_t p0 = dm.AllocatePage();
    std::cout << "Allocated page " << p0 << "\n";
    page_id_t p1 = dm.AllocatePage();
    std::cout << "Allocated page " << p1 << "\n";
    page_id_t p2 = dm.AllocatePage();
    std::cout << "Allocated page " << p2 << "\n";

    // Fill with distinct patterns
    std::array<std::byte, PAGE_SIZE> buf0, buf1, buf2;
    buf0.fill(std::byte{0xAA});
    buf1.fill(std::byte{0xBB});
    buf2.fill(std::byte{0xCC});

    dm.WritePage(p0, buf0.data()); std::cout << "Wrote page " << p0 << "\n";
    dm.WritePage(p1, buf1.data()); std::cout << "Wrote page " << p1 << "\n";
    dm.WritePage(p2, buf2.data()); std::cout << "Wrote page " << p2 << "\n";

    // Read back and verify
    std::array<std::byte, PAGE_SIZE> rbuf;
    auto verify = [&](page_id_t id, const std::array<std::byte, PAGE_SIZE>& expected) {
        dm.ReadPage(id, rbuf.data());
        bool ok = (rbuf == expected);
        std::cout << "Page " << id << ": " << (ok ? "OK" : "FAIL") << "\n";
    };
    verify(p0, buf0);
    verify(p1, buf1);
    verify(p2, buf2);

    return 0;
}
