#include <array>
#include <cstddef>
#include <cstdint>
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
        fd_ = open(db_file.c_str(), O_RDWR | O_CREAT | O_TRUNC, 0644);
        if (fd_ < 0)
            throw std::system_error(errno, std::system_category(), "DiskManager: open");
        num_pages_ = 0;
    }

    ~DiskManager() {
        if (fd_ >= 0) close(fd_);
    }

    page_id_t AllocatePage() {
        page_id_t id = num_pages_++;
        off_t new_size = static_cast<off_t>(num_pages_) * static_cast<off_t>(PAGE_SIZE);
        if (ftruncate(fd_, new_size) < 0)
            throw std::system_error(errno, std::system_category(), "DiskManager: ftruncate");
        return id;
    }

    void WritePage(page_id_t id, const std::byte* data) {
        off_t offset = static_cast<off_t>(id) * static_cast<off_t>(PAGE_SIZE);
        ssize_t w = pwrite(fd_, data, PAGE_SIZE, offset);
        if (w != static_cast<ssize_t>(PAGE_SIZE))
            throw std::runtime_error("DiskManager: pwrite incomplete");
    }

    void ReadPage(page_id_t id, std::byte* out) {
        off_t offset = static_cast<off_t>(id) * static_cast<off_t>(PAGE_SIZE);
        ssize_t r = pread(fd_, out, PAGE_SIZE, offset);
        if (r != static_cast<ssize_t>(PAGE_SIZE))
            throw std::runtime_error("DiskManager: pread incomplete");
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

    page_id_t p0 = dm.AllocatePage(); std::cout << "Allocated page " << p0 << "\n";
    page_id_t p1 = dm.AllocatePage(); std::cout << "Allocated page " << p1 << "\n";
    page_id_t p2 = dm.AllocatePage(); std::cout << "Allocated page " << p2 << "\n";

    std::array<std::byte, PAGE_SIZE> buf0, buf1, buf2;
    buf0.fill(std::byte{0xAA});
    buf1.fill(std::byte{0xBB});
    buf2.fill(std::byte{0xCC});

    dm.WritePage(p0, buf0.data()); std::cout << "Wrote page " << p0 << "\n";
    dm.WritePage(p1, buf1.data()); std::cout << "Wrote page " << p1 << "\n";
    dm.WritePage(p2, buf2.data()); std::cout << "Wrote page " << p2 << "\n";

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
