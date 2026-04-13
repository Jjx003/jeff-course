# Tips & Notes

## Opening the file

```cpp
fd_ = open(path.c_str(), O_RDWR | O_CREAT | O_TRUNC, 0644);
if (fd_ < 0) throw std::system_error(errno, std::system_category(), "DiskManager: open");
```

`O_TRUNC` resets the file to zero length on open, giving a clean slate for the demo. In a real database you would omit `O_TRUNC` to reopen an existing db.

## AllocatePage with ftruncate

```cpp
page_id_t AllocatePage() {
    page_id_t id = num_pages_++;
    off_t new_size = static_cast<off_t>(num_pages_) * PAGE_SIZE;
    if (ftruncate(fd_, new_size) < 0)
        throw std::system_error(errno, std::system_category(), "ftruncate");
    return id;
}
```

## Checking pwrite/pread return values

```cpp
ssize_t written = pwrite(fd_, data, PAGE_SIZE, offset);
if (written != static_cast<ssize_t>(PAGE_SIZE))
    throw std::runtime_error("DiskManager: pwrite incomplete");
```

Always check — `pwrite` can return fewer bytes if the disk is full or a signal interrupted the call.

## Computing the file offset

```cpp
off_t offset = static_cast<off_t>(id) * static_cast<off_t>(PAGE_SIZE);
```

Cast to `off_t` (which is 64-bit on 64-bit systems) before multiplying. A 32-bit `page_id_t` × 32-bit `PAGE_SIZE` overflows at 1 million pages (4 GB file) if you stay in 32-bit arithmetic.

## Verifying round-trips

Fill an entire `std::array<std::byte, PAGE_SIZE>` with a pattern, write it, read it back, compare byte-for-byte:

```cpp
bool all_match = std::equal(written_buf.begin(), written_buf.end(), read_buf.begin());
std::cout << "Page " << id << ": " << (all_match ? "OK" : "FAIL") << "\n";
```

## Cleanup

Delete `/tmp/test_disk.db` after the demo if you want a clean slate across runs:

```cpp
std::remove("/tmp/test_disk.db");
```

Or let `O_TRUNC` handle it on the next open.
