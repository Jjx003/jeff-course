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
// DiskManager (from module 05)
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
        off_t new_size = static_cast<off_t>(num_pages_) * PAGE_SIZE;
        if (ftruncate(fd_, new_size) < 0)
            throw std::system_error(errno, std::system_category(), "ftruncate");
        return id;
    }
    void WritePage(page_id_t id, const std::byte* data) {
        ssize_t w = pwrite(fd_, data, PAGE_SIZE,
                           static_cast<off_t>(id) * PAGE_SIZE);
        if (w != static_cast<ssize_t>(PAGE_SIZE))
            throw std::runtime_error("DiskManager: pwrite incomplete");
    }
    void ReadPage(page_id_t id, std::byte* out) {
        ssize_t r = pread(fd_, out, PAGE_SIZE,
                          static_cast<off_t>(id) * PAGE_SIZE);
        if (r != static_cast<ssize_t>(PAGE_SIZE))
            throw std::runtime_error("DiskManager: pread incomplete");
    }
    page_id_t NumPages() const { return num_pages_; }

private:
    int       fd_{-1};
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
// BufferPoolManager
// ---------------------------------------------------------------------------

class BufferPoolManager {
public:
    BufferPoolManager(size_t num_frames, DiskManager* dm)
        : frames_(num_frames), dm_(dm) {
        for (size_t i = 0; i < num_frames; ++i) free_list_.push(i);
    }

    Frame* FetchPage(page_id_t id) {
        // Cache hit
        if (auto it = page_table_.find(id); it != page_table_.end()) {
            frame_id_t fid = it->second;
            Frame& f = frames_[fid];
            f.pin_count++;
            // Now pinned, so it is no longer an eviction candidate.
            RemoveFromLRU(fid);
            std::cout << "FetchPage " << id << ": hit frame " << fid << "\n";
            return &f;
        }

        // Cache miss — get a frame
        frame_id_t fid;
        if (!free_list_.empty()) {
            fid = free_list_.front();
            free_list_.pop();
        } else {
            // The LRU list holds only unpinned frames; the back is the victim.
            if (lru_list_.empty()) return nullptr;  // all frames pinned
            fid = lru_list_.back();

            Frame& victim = frames_[fid];
            std::cout << "FetchPage " << id << ": miss, evicting page "
                      << victim.page_id << " from frame " << fid << "\n";
            if (victim.is_dirty) {
                dm_->WritePage(victim.page_id, victim.data.data());
                std::cout << "Evicted page " << victim.page_id << " (dirty, flushed)\n";
            } else {
                std::cout << "Evicted page " << victim.page_id << " (clean)\n";
            }
            page_table_.erase(victim.page_id);
            RemoveFromLRU(fid);
        }

        Frame& f = frames_[fid];
        dm_->ReadPage(id, f.data.data());
        f.page_id   = id;
        f.pin_count = 1;
        f.is_dirty  = false;
        page_table_[id] = fid;

        std::cout << "FetchPage " << id << ": loaded page " << id
                  << " into frame " << fid << "\n";
        return &f;
    }

    void UnpinPage(page_id_t id, bool is_dirty) {
        auto it = page_table_.find(id);
        if (it == page_table_.end()) return;
        frame_id_t fid = it->second;
        Frame& f = frames_[fid];
        if (f.pin_count <= 0) return;
        if (is_dirty) f.is_dirty = true;
        f.pin_count--;
        std::cout << "UnpinPage " << id << " dirty=" << (is_dirty ? "true" : "false") << "\n";
        // Reaching pin_count 0 makes the frame eviction-eligible.
        if (f.pin_count == 0) AddToLRU(fid);
    }

    bool FlushPage(page_id_t id) {
        auto it = page_table_.find(id);
        if (it == page_table_.end()) return false;
        Frame& f = frames_[it->second];
        if (f.is_dirty) {
            dm_->WritePage(id, f.data.data());
            f.is_dirty = false;
            std::cout << "FlushPage " << id << ": wrote to disk\n";
        } else {
            std::cout << "FlushPage " << id << ": dirty=false, no write needed\n";
        }
        return true;
    }

    Frame* NewPage(page_id_t& page_id_out) {
        frame_id_t fid;
        if (!free_list_.empty()) {
            fid = free_list_.front();
            free_list_.pop();
        } else {
            if (lru_list_.empty()) return nullptr;
            fid = lru_list_.back();
            Frame& victim = frames_[fid];
            if (victim.is_dirty) dm_->WritePage(victim.page_id, victim.data.data());
            page_table_.erase(victim.page_id);
            RemoveFromLRU(fid);
        }

        page_id_t new_id = dm_->AllocatePage();
        Frame& f = frames_[fid];
        f.data.fill(std::byte{0});
        f.page_id   = new_id;
        f.pin_count = 1;
        f.is_dirty  = false;
        page_table_[new_id] = fid;

        page_id_out = new_id;
        std::cout << "NewPage: allocated page " << new_id << " in frame " << fid << "\n";
        return &f;
    }

private:
    // The eviction list holds only unpinned (eviction-eligible) frames.
    // Front = most recently unpinned, back = least recently used.
    void AddToLRU(frame_id_t fid) {
        if (lru_map_.count(fid)) return;
        lru_list_.push_front(fid);
        lru_map_[fid] = lru_list_.begin();
    }

    void RemoveFromLRU(frame_id_t fid) {
        auto it = lru_map_.find(fid);
        if (it == lru_map_.end()) return;
        lru_list_.erase(it->second);
        lru_map_.erase(it);
    }

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

    // Allocate two pages
    page_id_t pid0, pid1;
    Frame* f0 = bpm.NewPage(pid0);
    Frame* f1 = bpm.NewPage(pid1);
    (void)f0; (void)f1;

    // Both pinned — fetch page 0 (hit)
    bpm.FetchPage(pid0);

    // Unpin both
    bpm.UnpinPage(pid0, false);
    bpm.UnpinPage(pid0, false);  // pin_count was 2 (NewPage + FetchPage)
    bpm.UnpinPage(pid1, false);

    // Fetch page 2 (new) — forces eviction of LRU unpinned page
    // (We need page 2 on disk first)
    page_id_t pid2 = dm.AllocatePage();
    // Write a pattern so ReadPage succeeds
    std::array<std::byte, PAGE_SIZE> buf;
    buf.fill(std::byte{0x42});
    dm.WritePage(pid2, buf.data());

    bpm.FetchPage(pid2);

    // Fetch page 1 (still in pool after eviction of page 0)
    bpm.FetchPage(pid1);

    // Pool is now full and both frames pinned — FetchPage should return nullptr
    // Try to fetch another new page
    page_id_t pid3 = dm.AllocatePage();
    buf.fill(std::byte{0x43});
    dm.WritePage(pid3, buf.data());
    Frame* null_f = bpm.FetchPage(pid3);
    std::cout << "pool full test: " << (null_f == nullptr ? "nullptr (all pinned)" : "got frame") << "\n";

    // Unpin page 2 and flush it
    bpm.UnpinPage(pid2, false);
    bpm.FlushPage(pid2);

    return 0;
}
