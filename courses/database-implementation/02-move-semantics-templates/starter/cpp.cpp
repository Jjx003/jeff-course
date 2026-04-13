#include <array>
#include <cassert>
#include <concepts>
#include <cstddef>
#include <iostream>
#include <string>
#include <type_traits>

// ---------------------------------------------------------------------------
// Part 1: Buffer<T> — move-only heap buffer
// ---------------------------------------------------------------------------

template<typename T>
class Buffer {
public:
    explicit Buffer(size_t size) {
        // TODO: allocate size * sizeof(T) bytes with new T[size]
        //       set data_, size_, cap_ = size
    }

    ~Buffer() {
        // TODO: delete[] data_
    }

    // Non-copyable
    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;

    Buffer(Buffer&& other) noexcept {
        // TODO: steal data_, size_, cap_ from other
        //       zero out other.data_, other.size_, other.cap_
        //       print "Buffer moved: source size=0"
    }

    Buffer& operator=(Buffer&& other) noexcept {
        // TODO: guard against self-assignment
        //       free current data_
        //       steal from other, zero other
        //       print "Buffer moved: source size=0"
        return *this;
    }

    T*     Data() const { return data_; }
    size_t Size() const { return size_; }

private:
    T*     data_{nullptr};
    size_t size_{0};
    size_t cap_{0};
};

// ---------------------------------------------------------------------------
// Part 2: RingBuffer<T, N> — fixed-capacity circular queue
// ---------------------------------------------------------------------------

template<typename T, size_t N>
class RingBuffer {
public:
    // TODO: push val; return false if full
    bool push(const T& val) {
        return false;
    }

    // TODO: pop into out; return false if empty
    bool pop(T& out) {
        return false;
    }

    bool empty() const {
        // TODO
        return true;
    }

    bool full() const {
        // TODO
        return false;
    }

    size_t size() const {
        // TODO
        return 0;
    }

private:
    std::array<T, N> data_{};
    size_t head_{0};
    size_t tail_{0};
    size_t count_{0};
};

// ---------------------------------------------------------------------------
// Part 3: to_string_if_arithmetic — if constexpr dispatch
// ---------------------------------------------------------------------------

template<typename T>
std::string to_string_if_arithmetic(const T& val) {
    // TODO: if T is arithmetic, return std::to_string(val)
    //       else return "<non-arithmetic>"
    //       Use if constexpr, NOT SFINAE
    return "";
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    // --- Buffer ---
    Buffer<int> src(4);
    std::cout << "Buffer<int> size=" << src.Size() << "\n";

    Buffer<int> dst(std::move(src));
    std::cout << "After move: src.Size()=" << src.Size()
              << " dst.Size()=" << dst.Size() << "\n";

    // --- RingBuffer ---
    RingBuffer<int, 4> rb;
    rb.push(10); rb.push(20); rb.push(30);
    std::cout << "RingBuffer push: 10 20 30\n";

    int val;
    rb.pop(val);
    std::cout << "RingBuffer pop: " << val << "\n";
    std::cout << "RingBuffer size: " << rb.size() << "\n";

    // --- to_string_if_arithmetic ---
    std::cout << "to_string(42): "     << to_string_if_arithmetic(42)          << "\n";
    std::cout << "to_string(3.14): "   << to_string_if_arithmetic(3.14)        << "\n";
    std::cout << "to_string(string): " << to_string_if_arithmetic(std::string("hi")) << "\n";

    return 0;
}
