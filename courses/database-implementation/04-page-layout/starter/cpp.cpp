#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>

// ---------------------------------------------------------------------------
// ByteSpan — a minimal non-owning view over a run of bytes.
// (std::span is C++20; this keeps the module compilable under -std=c++17.)
// ---------------------------------------------------------------------------

struct ByteSpan {
    const std::byte* ptr{nullptr};
    size_t           len{0};

    const std::byte* data() const { return ptr; }
    size_t           size() const { return len; }
    bool             empty() const { return len == 0; }
};

// ---------------------------------------------------------------------------
// Page — slotted-page layout
// ---------------------------------------------------------------------------

class Page {
public:
    static constexpr size_t SIZE = 4096;

    Page() {
        // TODO: zero-initialise data_ (or rely on default array init)
        //       write num_slots = 0 at offset 0
        //       write free_space_offset = 4096 at offset 2
    }

    // Insert tuple; return slot_id or -1 if no space.
    int InsertTuple(const std::byte* data, uint16_t len) {
        // TODO:
        // 1. Check FreeSpace() >= 4 + len
        // 2. Decrement free_space_offset by len
        // 3. memcpy data into data_ at free_space_offset
        // 4. Write slot {free_space_offset, len} at index num_slots
        // 5. Increment num_slots
        // 6. Return old num_slots (the new slot id)
        return -1;
    }

    // Return a view over tuple bytes; empty view if deleted or out of range.
    ByteSpan GetTuple(uint16_t slot_id) const {
        // TODO
        return {};
    }

    // Mark slot deleted (set length = 0). No-op if out of range.
    void DeleteTuple(uint16_t slot_id) {
        // TODO
    }

    // Free bytes available for new inserts.
    uint16_t FreeSpace() const {
        // TODO: return free_space_offset - (4 + num_slots * 4)
        return 0;
    }

private:
    // --- helper accessors for header and slot array ---

    uint16_t GetNumSlots() const {
        uint16_t n;
        std::memcpy(&n, data_.data(), sizeof(n));
        return n;
    }
    void SetNumSlots(uint16_t n) {
        std::memcpy(data_.data(), &n, sizeof(n));
    }

    uint16_t GetFreeSpaceOffset() const {
        uint16_t o;
        std::memcpy(&o, data_.data() + 2, sizeof(o));
        return o;
    }
    void SetFreeSpaceOffset(uint16_t o) {
        std::memcpy(data_.data() + 2, &o, sizeof(o));
    }

    struct Slot { uint16_t offset; uint16_t length; };

    Slot GetSlot(uint16_t i) const {
        Slot s;
        std::memcpy(&s, data_.data() + 4 + i * 4, sizeof(Slot));
        return s;
    }
    void SetSlot(uint16_t i, Slot s) {
        std::memcpy(data_.data() + 4 + i * 4, &s, sizeof(Slot));
    }

    std::array<std::byte, SIZE> data_{};
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    Page page;

    // Insert three tuples
    auto insert_str = [&](const char* s) -> int {
        std::string_view sv(s);
        return page.InsertTuple(
            reinterpret_cast<const std::byte*>(sv.data()),
            static_cast<uint16_t>(sv.size()));
    };

    int s0 = insert_str("Hello");
    int s1 = insert_str("World!");
    int s2 = insert_str("DB");

    auto print_slot = [&](int sid) {
        auto sp = page.GetTuple(static_cast<uint16_t>(sid));
        if (sp.empty()) {
            std::cout << "<deleted>\n";
        } else {
            std::cout << std::string_view(reinterpret_cast<const char*>(sp.data()), sp.size()) << "\n";
        }
    };

    std::cout << "Inserted slot " << s0 << ": "; print_slot(s0);
    std::cout << "Inserted slot " << s1 << ": "; print_slot(s1);
    std::cout << "Inserted slot " << s2 << ": "; print_slot(s2);

    std::cout << "FreeSpace before delete: " << page.FreeSpace() << "\n";

    page.DeleteTuple(static_cast<uint16_t>(s1));
    std::cout << "Deleted slot " << s1 << "\n";
    std::cout << "FreeSpace after delete: " << page.FreeSpace() << "\n";

    std::cout << "GetTuple(1) after delete: "; print_slot(1);
    std::cout << "GetTuple(0): "; print_slot(0);
    std::cout << "GetTuple(2): "; print_slot(2);

    return 0;
}
