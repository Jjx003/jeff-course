# Tips & Notes

## The LRU list and iterator map together

The key data structure: a `std::list<frame_id_t>` plus a `std::unordered_map<frame_id_t, list::iterator>`.

- Move to front: `lru_list_.splice(lru_list_.begin(), lru_list_, lru_map_[frame_id])` — O(1).
- Remove: `lru_list_.erase(lru_map_[frame_id]); lru_map_.erase(frame_id)` — O(1).
- Evict from back: iterate from `lru_list_.rbegin()` to find the first with `pin_count == 0`.

Only **unpinned** frames (pin_count == 0) should be in the LRU list. A pinned frame is not eviction-eligible and should not be on the list.

## FetchPage flow

```
if page_id in page_table:
    frame = frames_[page_table_[page_id]]
    frame.pin_count++
    move frame to front of LRU list
    return &frame

// miss: need a free or evictable frame
frame = find_victim()   // scan LRU back to front, find pin_count==0
if no victim: return nullptr

if frame.is_dirty: FlushPage(frame.page_id)
page_table_.erase(frame.page_id)
remove from lru_map_

dm_->ReadPage(page_id, frame.data.data())
frame.page_id = page_id
frame.pin_count = 1
frame.is_dirty = false
page_table_[page_id] = frame_id
add to front of LRU list (but frame is pinned — depends on your design)
return &frame
```

Note: some implementations only add to the LRU list when `pin_count` drops to 0. Both approaches are correct; be consistent.

## NewPage flow

```
frame = find_victim()  // same eviction logic
if no victim: return nullptr

new_id = dm_->AllocatePage()
if frame.is_dirty: flush frame.page_id
reset frame: page_id = new_id, pin_count = 1, is_dirty = false
page_table_[new_id] = frame_id
page_id_out = new_id
return &frame
```

## Free frames at startup

All frames start free. Keep a `std::queue<frame_id_t> free_list_` initialised with `{0, 1, ..., num_frames-1}`. `FetchPage` drains the free list before resorting to LRU eviction — free frames are always preferred over eviction.

## Debugging tip

Print `pin_count` on every `FetchPage`/`UnpinPage` call during development. A common bug: forgetting to unpin a page in the calling code, exhausting all frames and causing every subsequent `FetchPage` to return `nullptr`.
