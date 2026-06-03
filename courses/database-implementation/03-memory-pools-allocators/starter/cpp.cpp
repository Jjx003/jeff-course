#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <memory_resource>
#include <new>

// ---------------------------------------------------------------------------
// Part 1: SlabAllocator<T, PoolSize>
// ---------------------------------------------------------------------------

template<typename T, size_t PoolSize>
class SlabAllocator {
    static_assert(sizeof(T) >= sizeof(void*),
                  "SlabAllocator: T must be at least pointer-sized for free-list");
public:
    SlabAllocator() {
        // TODO: allocate PoolSize * sizeof(T) bytes aligned to alignof(T)
        //       using ::operator new(size, std::align_val_t{alignof(T)})
        //       build the free list by linking each slot to the next
        //       set free_list_ to the first slot, available_ = PoolSize
    }

    ~SlabAllocator() {
        // TODO: free pool_ with ::operator delete(pool_, std::align_val_t{alignof(T)})
    }

    T* allocate() {
        // TODO: pop from free_list_
        //       if free_list_ == nullptr, return nullptr
        //       placement-new construct T() in the slot
        //       print "Allocated @ 0x<hex>"
        //       decrement available_
        return nullptr;
    }

    void deallocate(T* ptr) {
        // TODO: call ptr->~T() explicitly
        //       push ptr back onto free_list_
        //       print "Deallocated @ 0x<hex>"
        //       increment available_
    }

    size_t available() const { return available_; }

private:
    T*     pool_{nullptr};
    void*  free_list_{nullptr};
    size_t available_{0};
};

// ---------------------------------------------------------------------------
// Part 2: PoolResource — std::pmr::memory_resource backed by a slab
// ---------------------------------------------------------------------------

// Use aligned_storage to hold 64-byte blocks
struct alignas(64) Block64 { char data[64]; };

class PoolResource : public std::pmr::memory_resource {
public:
    PoolResource() = default;

protected:
    void* do_allocate(size_t bytes, size_t /*alignment*/) override {
        // TODO: assert bytes <= sizeof(Block64)
        //       allocate a Block64 from slab_, return it as void*
        return nullptr;
    }

    void do_deallocate(void* ptr, size_t /*bytes*/, size_t /*alignment*/) override {
        // TODO: deallocate ptr back to slab_
    }

    bool do_is_equal(const std::pmr::memory_resource& other) const noexcept override {
        // TODO: return this == &other
        return false;
    }

private:
    SlabAllocator<Block64, 16> slab_;
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    // --- SlabAllocator demo ---
    // T must be at least pointer-sized so a free slot can hold the free-list
    // next-pointer (see the static_assert), so the demo uses int64_t.
    SlabAllocator<int64_t, 8> alloc;

    std::array<int64_t*, 4> ptrs{};
    for (int i = 0; i < 4; ++i) {
        ptrs[i] = alloc.allocate();
        *ptrs[i] = i * 10;
    }

    // Deallocate indices 1 and 2
    alloc.deallocate(ptrs[1]);
    alloc.deallocate(ptrs[2]);

    // Re-allocate 2 — should reuse ptrs[2] then ptrs[1] (LIFO)
    int64_t* r0 = alloc.allocate();
    int64_t* r1 = alloc.allocate();

    bool reused = (r0 == ptrs[2] || r0 == ptrs[1]) &&
                  (r1 == ptrs[2] || r1 == ptrs[1]);
    std::cout << "Addresses reused: " << (reused ? "yes" : "no") << "\n";

    // Clean up remaining allocations
    alloc.deallocate(ptrs[0]);
    alloc.deallocate(r0);
    alloc.deallocate(r1);
    alloc.deallocate(ptrs[3]);

    // --- pmr::vector demo ---
    {
        PoolResource pool;
        std::pmr::vector<int> v{&pool};
        v.push_back(1);
        v.push_back(2);
        v.push_back(3);
        std::cout << "pmr::vector values:";
        for (int x : v) std::cout << " " << x;
        std::cout << "\n";
    }

    return 0;
}
