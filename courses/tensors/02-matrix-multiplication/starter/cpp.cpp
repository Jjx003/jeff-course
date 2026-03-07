#include <cassert>
#include <iostream>
#include <stdexcept>
#include <vector>

// ── Minimal Tensor (copy your implementation from problem 1) ─────────────────
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

    double at(int i, int j) const {
        return data[i * strides[0] + j * strides[1]];
    }

    void set(int i, int j, double v) {
        data[i * strides[0] + j * strides[1]] = v;
    }
};

// ── Your implementation ──────────────────────────────────────────────────────

/**
 * Multiply A (m×k) by B (k×n) and return C (m×n).
 *
 * TODO: validate inner dimensions, allocate output, implement triple loop.
 */
Tensor matmul(const Tensor& A, const Tensor& B) {
    int m = A.shape[0], k = A.shape[1];
    int k2 = B.shape[0], n = B.shape[1];

    if (k != k2) {
        throw std::invalid_argument(
            "matmul: inner dimensions must match, got " +
            std::to_string(k) + " vs " + std::to_string(k2));
    }

    // TODO: allocate C of shape (m, n) with zeros
    // TODO: triple loop: for i, for j, for l → C[i,j] += A[i,l] * B[l,j]
    throw std::logic_error("matmul: not implemented");
}

// ── Smoke test ───────────────────────────────────────────────────────────────
int main() {
    Tensor A({1, 2, 3, 4, 5, 6}, {2, 3});
    Tensor B({7, 8, 9, 10, 11, 12}, {3, 2});

    Tensor C = matmul(A, B);
    std::cout << "C[0,0] = " << C.at(0, 0) << "\n";  // 58
    std::cout << "C[0,1] = " << C.at(0, 1) << "\n";  // 64
    std::cout << "C[1,0] = " << C.at(1, 0) << "\n";  // 139
    std::cout << "C[1,1] = " << C.at(1, 1) << "\n";  // 154
    return 0;
}
