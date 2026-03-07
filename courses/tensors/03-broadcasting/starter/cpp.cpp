#include <algorithm>
#include <cassert>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <vector>

// ── Minimal Tensor ────────────────────────────────────────────────────────────
class Tensor {
public:
    std::vector<double> data;
    std::vector<int>    shape;
    std::vector<int>    strides;

    Tensor(std::vector<double> data, std::vector<int> shape)
        : data(std::move(data)), shape(std::move(shape))
    {
        strides.resize(this->shape.size());
        int s = 1;
        for (int i = (int)this->shape.size() - 1; i >= 0; --i) {
            strides[i] = s;
            s *= this->shape[i];
        }
    }

    double at(const std::vector<int>& idx) const {
        int off = 0;
        for (int i = 0; i < (int)idx.size(); ++i) off += idx[i] * strides[i];
        return data[off];
    }

    void set(const std::vector<int>& idx, double v) {
        int off = 0;
        for (int i = 0; i < (int)idx.size(); ++i) off += idx[i] * strides[i];
        data[off] = v;
    }

    int numel() const {
        int n = 1;
        for (int d : shape) n *= d;
        return n;
    }
};

// ── Your implementation ───────────────────────────────────────────────────────

/**
 * Compute broadcast output shape.
 * Raises std::invalid_argument for incompatible shapes.
 *
 * TODO: implement broadcasting rules.
 */
std::vector<int> broadcastShapes(
    const std::vector<int>& a,
    const std::vector<int>& b)
{
    throw std::logic_error("broadcastShapes: not implemented");
}

/**
 * Add two tensors with broadcasting.
 *
 * TODO: implement broadcast_add.
 */
Tensor broadcastAdd(const Tensor& A, const Tensor& B) {
    throw std::logic_error("broadcastAdd: not implemented");
}

// ── Smoke test ────────────────────────────────────────────────────────────────
int main() {
    // Test 1: scalar broadcast
    Tensor a({1, 2, 3}, {3});
    Tensor b({10}, {1});
    Tensor c = broadcastAdd(a, b);
    std::cout << "Test 1: ";
    for (double v : c.data) std::cout << v << " ";
    std::cout << "\n";  // 11 12 13

    // Test 2: row + column
    Tensor row({1, 2, 3}, {1, 3});
    Tensor col({10, 20}, {2, 1});
    Tensor out = broadcastAdd(row, col);
    std::cout << "Test 2: ";
    for (double v : out.data) std::cout << v << " ";
    std::cout << "\n";  // 11 12 13 21 22 23

    return 0;
}
