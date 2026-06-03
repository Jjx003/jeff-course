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
        pool_ = static_cast<T*>(
            ::operator new(PoolSize * sizeof(T), std::align_val_t{alignof(T)}));
        // Build free list
        for (size_t i = 0; i < PoolSize - 1; ++i) {
            void* slot = static_cast<void*>(pool_ + i);
            *reinterpret_cast<void**>(slot) = static_cast<void*>(pool_ + i + 1);
        }
        *reinterpret_cast<void**>(pool_ + PoolSize - 1) = nullptr;
        free_list_  = static_cast<void*>(pool_);
        available_  = PoolSize;
    }

    ~SlabAllocator() {
        ::operator delete(pool_, std::align_val_t{alignof(T)});
    }

    T* allocate() {
        if (!free_list_) return nullptr;
        void* slot    = free_list_;
        free_list_    = *reinterpret_cast<void**>(slot);
        T* obj        = new(slot) T();
        --available_;
        std::cout << "Allocated @ 0x"
                  << std::hex << reinterpret_cast<uintptr_t>(obj) << std::dec << "\n";
        return obj;
    }

    void deallocate(T* ptr) {
        std::cout << "Deallocated @ 0x"
                  << std::hex << reinterpret_cast<uintptr_t>(ptr) << std::dec << "\n";
        ptr->~T();
        *reinterpret_cast<void**>(ptr) = free_list_;
        free_list_ = static_cast<void*>(ptr);
        ++available_;
    }

    size_t available() const { return available_; }

private:
    T*     pool_{nullptr};
    void*  free_list_{nullptr};
    size_t available_{0};
};

// ---------------------------------------------------------------------------
// Part 2: PoolResource
// ---------------------------------------------------------------------------

struct alignas(64) Block64 { char data[64]; };

class PoolResource : public std::pmr::memory_resource {
public:
    PoolResource() = default;

protected:
    void* do_allocate(size_t bytes, size_t /*alignment*/) override {
        assert(bytes <= sizeof(Block64) && "PoolResource: request exceeds block size");
        Block64* b = slab_.allocate();
        if (!b) throw std::bad_alloc{};
        return b;
    }

    void do_deallocate(void* ptr, size_t /*bytes*/, size_t /*alignment*/) override {
        slab_.deallocate(static_cast<Block64*>(ptr));
    }

    bool do_is_equal(const std::pmr::memory_resource& other) const noexcept override {
        return this == &other;
    }

private:
    SlabAllocator<Block64, 16> slab_;
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    // T must be at least pointer-sized so a free slot can hold the
    // next-pointer of the free list (see the static_assert above), so the
    // demo uses int64_t rather than int.
    SlabAllocator<int64_t, 8> alloc;

    std::array<int64_t*, 4> ptrs{};
    for (int i = 0; i < 4; ++i) {
        ptrs[i] = alloc.allocate();
        *ptrs[i] = i * 10;
    }

    alloc.deallocate(ptrs[1]);
    alloc.deallocate(ptrs[2]);

    int64_t* r0 = alloc.allocate();
    int64_t* r1 = alloc.allocate();

    bool reused = (r0 == ptrs[2] || r0 == ptrs[1]) &&
                  (r1 == ptrs[2] || r1 == ptrs[1]);
    std::cout << "Addresses reused: " << (reused ? "yes" : "no") << "\n";

    alloc.deallocate(ptrs[0]);
    alloc.deallocate(r0);
    alloc.deallocate(r1);
    alloc.deallocate(ptrs[3]);

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
