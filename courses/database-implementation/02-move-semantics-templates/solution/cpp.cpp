#include <array>
#include <cstddef>
#include <iostream>
#include <string>
#include <type_traits>

// ---------------------------------------------------------------------------
// Part 1: Buffer<T>
// ---------------------------------------------------------------------------

template<typename T>
class Buffer {
public:
    explicit Buffer(size_t size)
        : data_(new T[size]), size_(size), cap_(size) {}

    ~Buffer() { delete[] data_; }

    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;

    Buffer(Buffer&& other) noexcept
        : data_(other.data_), size_(other.size_), cap_(other.cap_) {
        other.data_ = nullptr;
        other.size_ = 0;
        other.cap_  = 0;
        std::cout << "Buffer moved: source size=0\n";
    }

    Buffer& operator=(Buffer&& other) noexcept {
        if (this == &other) return *this;
        delete[] data_;
        data_  = other.data_;
        size_  = other.size_;
        cap_   = other.cap_;
        other.data_ = nullptr;
        other.size_ = 0;
        other.cap_  = 0;
        std::cout << "Buffer moved: source size=0\n";
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
// Part 2: RingBuffer<T, N>
// ---------------------------------------------------------------------------

template<typename T, size_t N>
class RingBuffer {
public:
    bool push(const T& val) {
        if (count_ == N) return false;
        data_[tail_] = val;
        tail_ = (tail_ + 1) % N;
        ++count_;
        return true;
    }

    bool pop(T& out) {
        if (count_ == 0) return false;
        out   = data_[head_];
        head_ = (head_ + 1) % N;
        --count_;
        return true;
    }

    bool   empty() const { return count_ == 0; }
    bool   full()  const { return count_ == N; }
    size_t size()  const { return count_; }

private:
    std::array<T, N> data_{};
    size_t head_{0};
    size_t tail_{0};
    size_t count_{0};
};

// ---------------------------------------------------------------------------
// Part 3: to_string_if_arithmetic
// ---------------------------------------------------------------------------

template<typename T>
std::string to_string_if_arithmetic(const T& val) {
    if constexpr (std::is_arithmetic_v<T>) {
        return std::to_string(val);
    } else {
        return "<non-arithmetic>";
    }
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    // Buffer
    Buffer<int> src(4);
    std::cout << "Buffer<int> size=" << src.Size() << "\n";

    Buffer<int> dst(std::move(src));
    std::cout << "After move: src.Size()=" << src.Size()
              << " dst.Size()=" << dst.Size() << "\n";

    // RingBuffer
    RingBuffer<int, 4> rb;
    rb.push(10); rb.push(20); rb.push(30);
    std::cout << "RingBuffer push: 10 20 30\n";

    int val;
    rb.pop(val);
    std::cout << "RingBuffer pop: " << val << "\n";
    std::cout << "RingBuffer size: " << rb.size() << "\n";

    // to_string_if_arithmetic
    std::cout << "to_string(42): "     << to_string_if_arithmetic(42)               << "\n";
    std::cout << "to_string(3.14): "   << to_string_if_arithmetic(3.14)             << "\n";
    std::cout << "to_string(string): " << to_string_if_arithmetic(std::string("hi")) << "\n";

    return 0;
}
