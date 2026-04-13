# Buffer Pool Manager

## Your Task

Implement `BufferPoolManager` — a fixed-size cache of disk pages in memory. All higher-level components (table heap, B+ tree, executor) go through the buffer pool to read and write pages.

### Data structures

```cpp
using frame_id_t = size_t;

struct Frame {
    std::array<std::byte, PAGE_SIZE> data{};
    page_id_t page_id{INVALID_PAGE_ID};
    int       pin_count{0};
    bool      is_dirty{false};
};
```

```cpp
class BufferPoolManager {
public:
    BufferPoolManager(size_t num_frames, DiskManager* dm);

    // Return pointer to the frame holding page id.
    // Load from disk if not in pool; evict LRU unpinned frame if pool is full.
    // Returns nullptr if all frames are pinned (eviction impossible).
    // Increments pin_count.
    Frame* FetchPage(page_id_t id);

    // Decrement pin_count. Mark dirty if is_dirty=true.
    // If pin_count reaches 0, the frame becomes eviction-eligible.
    void UnpinPage(page_id_t id, bool is_dirty);

    // Write frame to disk if dirty. Does not evict.
    bool FlushPage(page_id_t id);

    // Allocate a new page on disk, load into a frame, return it pinned.
    Frame* NewPage(page_id_t& page_id_out);

private:
    std::vector<Frame>                        frames_;
    std::unordered_map<page_id_t, frame_id_t> page_table_;
    std::list<frame_id_t>                     lru_list_;   // front = MRU, back = LRU
    std::unordered_map<frame_id_t, std::list<frame_id_t>::iterator> lru_map_;
    DiskManager*                              dm_;
};
```

### LRU policy

Maintain a doubly-linked list (use `std::list`) where:
- Front = most recently used.
- Back = least recently used.

On `FetchPage` (hit or miss): move the frame to the front.
On `UnpinPage` to 0: the frame is now eviction-eligible — add it to the front if not already present.

**Eviction:** scan from the back of the list to find the first frame with `pin_count == 0`. If `is_dirty`, flush before eviction. Remove from page table, reset frame fields.

### Constants

```cpp
constexpr page_id_t INVALID_PAGE_ID = std::numeric_limits<page_id_t>::max();
```

## What to Print

```
NewPage: allocated page 0 in frame 0
NewPage: allocated page 1 in frame 1
FetchPage 0: hit frame 0
UnpinPage 0 dirty=false
UnpinPage 1 dirty=false
FetchPage 2: miss, evicting page 0 from frame 0
Evicted page 0 (clean)
FetchPage 2: loaded page 2 into frame 0
FetchPage 1: hit frame 1
pool full test: nullptr (all pinned)
FlushPage 2: dirty=false, no write needed
```

## Constraints

- Compile with `g++ -std=c++20 -Wall -Wextra`.
- Pool size = 2 frames in the demo.
- Reuse the `DiskManager` from module 05 (copy its implementation into this file or `#include` it).
