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
        data_.fill(std::byte{0});
        SetNumSlots(0);
        SetFreeSpaceOffset(static_cast<uint16_t>(SIZE));
    }

    int InsertTuple(const std::byte* data, uint16_t len) {
        if (FreeSpace() < static_cast<uint16_t>(4 + len)) return -1;

        uint16_t fso = GetFreeSpaceOffset();
        fso -= len;
        std::memcpy(data_.data() + fso, data, len);
        SetFreeSpaceOffset(fso);

        uint16_t ns = GetNumSlots();
        SetSlot(ns, {fso, len});
        SetNumSlots(static_cast<uint16_t>(ns + 1));
        return ns;
    }

    ByteSpan GetTuple(uint16_t slot_id) const {
        if (slot_id >= GetNumSlots()) return {};
        Slot s = GetSlot(slot_id);
        if (s.length == 0) return {};
        return {data_.data() + s.offset, s.length};
    }

    void DeleteTuple(uint16_t slot_id) {
        if (slot_id >= GetNumSlots()) return;
        Slot s = GetSlot(slot_id);
        s.length = 0;
        SetSlot(slot_id, s);
    }

    uint16_t FreeSpace() const {
        uint16_t ns  = GetNumSlots();
        uint16_t fso = GetFreeSpaceOffset();
        return static_cast<uint16_t>(fso - (4 + ns * 4));
    }

private:
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

    // FreeSpace: 4096 - 4(header) - 3*4(slots) - 5 - 6 - 2 = 4096 - 4 - 12 - 13 = 4067
    // Wait: free_space_offset starts at 4096, after inserts = 4096 - 5 - 6 - 2 = 4083
    // num_slots = 3
    // FreeSpace = 4083 - (4 + 3*4) = 4083 - 16 = 4067
    std::cout << "FreeSpace before delete: " << page.FreeSpace() << "\n";

    page.DeleteTuple(static_cast<uint16_t>(s1));
    std::cout << "Deleted slot " << s1 << "\n";
    std::cout << "FreeSpace after delete: " << page.FreeSpace() << "\n";

    std::cout << "GetTuple(1) after delete: "; print_slot(1);
    std::cout << "GetTuple(0): "; print_slot(0);
    std::cout << "GetTuple(2): "; print_slot(2);

    return 0;
}
