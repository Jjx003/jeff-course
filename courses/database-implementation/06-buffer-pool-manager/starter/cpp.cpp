#include <array>
#include <cstddef>
#include <cstdint>
#include <fcntl.h>
#include <iostream>
#include <limits>
#include <list>
#include <queue>
#include <stdexcept>
#include <string>
#include <system_error>
#include <unordered_map>
#include <vector>
#include <unistd.h>

// ---------------------------------------------------------------------------
// DiskManager (provided — do not modify)
// ---------------------------------------------------------------------------

using page_id_t  = uint32_t;
using frame_id_t = size_t;
constexpr size_t    PAGE_SIZE       = 4096;
constexpr page_id_t INVALID_PAGE_ID = std::numeric_limits<page_id_t>::max();

class DiskManager {
public:
    explicit DiskManager(const std::string& db_file) {
        fd_ = open(db_file.c_str(), O_RDWR | O_CREAT | O_TRUNC, 0644);
        if (fd_ < 0)
            throw std::system_error(errno, std::system_category(), "DiskManager: open");
    }
    ~DiskManager() { if (fd_ >= 0) close(fd_); }
    page_id_t AllocatePage() {
        page_id_t id = num_pages_++;
        if (ftruncate(fd_, static_cast<off_t>(num_pages_) * PAGE_SIZE) < 0)
            throw std::system_error(errno, std::system_category(), "ftruncate");
        return id;
    }
    void WritePage(page_id_t id, const std::byte* data) {
        if (pwrite(fd_, data, PAGE_SIZE, static_cast<off_t>(id)*PAGE_SIZE)
                != static_cast<ssize_t>(PAGE_SIZE))
            throw std::runtime_error("pwrite incomplete");
    }
    void ReadPage(page_id_t id, std::byte* out) {
        if (pread(fd_, out, PAGE_SIZE, static_cast<off_t>(id)*PAGE_SIZE)
                != static_cast<ssize_t>(PAGE_SIZE))
            throw std::runtime_error("pread incomplete");
    }
    page_id_t NumPages() const { return num_pages_; }
private:
    int fd_{-1};
    page_id_t num_pages_{0};
};

// ---------------------------------------------------------------------------
// Frame
// ---------------------------------------------------------------------------

struct Frame {
    std::array<std::byte, PAGE_SIZE> data{};
    page_id_t page_id{INVALID_PAGE_ID};
    int       pin_count{0};
    bool      is_dirty{false};
};

// ---------------------------------------------------------------------------
// BufferPoolManager — implement all methods
// ---------------------------------------------------------------------------

class BufferPoolManager {
public:
    BufferPoolManager(size_t num_frames, DiskManager* dm)
        : frames_(num_frames), dm_(dm) {
        // TODO: push all frame ids onto free_list_
    }

    // Return pinned frame for page id, loading from disk if needed.
    // Return nullptr if no evictable frame exists.
    Frame* FetchPage(page_id_t id) {
        // TODO
        return nullptr;
    }

    // Decrement pin count; mark dirty if is_dirty.
    void UnpinPage(page_id_t id, bool is_dirty) {
        // TODO
    }

    // If frame is dirty, write to disk and clear dirty flag.
    bool FlushPage(page_id_t id) {
        // TODO
        return false;
    }

    // Allocate new disk page, load into frame, return pinned.
    Frame* NewPage(page_id_t& page_id_out) {
        // TODO
        return nullptr;
    }

private:
    // TODO: helpers to add/remove a frame from lru_list_. The list holds only
    //       unpinned (eviction-eligible) frames: front = most recently
    //       unpinned, back = LRU victim. UnpinPage to 0 adds to the front;
    //       pinning a frame (Fetch/New) removes it; eviction takes the back.

    std::vector<Frame>                        frames_;
    std::unordered_map<page_id_t, frame_id_t> page_table_;
    std::list<frame_id_t>                     lru_list_;
    std::unordered_map<frame_id_t, std::list<frame_id_t>::iterator> lru_map_;
    std::queue<frame_id_t>                    free_list_;
    DiskManager*                              dm_;
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    DiskManager dm("/tmp/test_bpm.db");
    BufferPoolManager bpm(2, &dm);

    page_id_t pid0, pid1;
    Frame* f0 = bpm.NewPage(pid0);
    Frame* f1 = bpm.NewPage(pid1);
    (void)f0; (void)f1;

    bpm.FetchPage(pid0);
    bpm.UnpinPage(pid0, false);
    bpm.UnpinPage(pid0, false);
    bpm.UnpinPage(pid1, false);

    // Create page 2 on disk for FetchPage test
    page_id_t pid2 = dm.AllocatePage();
    std::array<std::byte, PAGE_SIZE> buf;
    buf.fill(std::byte{0x42});
    dm.WritePage(pid2, buf.data());

    bpm.FetchPage(pid2);
    bpm.FetchPage(pid1);

    // All frames pinned — should get nullptr
    page_id_t pid3 = dm.AllocatePage();
    buf.fill(std::byte{0x43});
    dm.WritePage(pid3, buf.data());
    Frame* null_f = bpm.FetchPage(pid3);
    std::cout << "pool full test: "
              << (null_f == nullptr ? "nullptr (all pinned)" : "got frame") << "\n";

    bpm.UnpinPage(pid2, false);
    bpm.FlushPage(pid2);

    return 0;
}
