#include <cassert>
#include <iostream>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <vector>

/**
 * Minimal Tensor class — shape + strides + flat data.
 *
 * TODO: implement the methods marked with TODO below.
 */
class Tensor {
public:
    std::vector<double>  data;
    std::vector<int>     shape;
    std::vector<int>     strides;

    Tensor(std::vector<double> data, std::vector<int> shape)
        : data(std::move(data)), shape(std::move(shape))
    {
        int expected = 1;
        for (int d : this->shape) expected *= d;
        assert((int)this->data.size() == expected &&
               "data length does not match shape");

        strides = computeStrides(this->shape);
    }

private:
    static std::vector<int> computeStrides(const std::vector<int>& shape) {
        std::vector<int> s(shape.size());
        // TODO: fill s with C-contiguous strides.
        // s.back() = 1, each earlier entry = next entry * next dim size.
        throw std::logic_error("computeStrides: not implemented");
        return s;
    }

public:
    double operator[](const std::vector<int>& indices) const {
        // TODO: compute flat offset = sum(indices[i] * strides[i])
        // and return data[offset].
        throw std::logic_error("operator[]: not implemented");
    }

    int numel() const {
        // TODO: return the total number of elements.
        throw std::logic_error("numel: not implemented");
    }

    std::string repr() const {
        std::ostringstream oss;
        oss << "Tensor(shape=[";
        for (size_t i = 0; i < shape.size(); ++i) {
            if (i) oss << ", ";
            oss << shape[i];
        }
        oss << "], strides=[";
        for (size_t i = 0; i < strides.size(); ++i) {
            if (i) oss << ", ";
            oss << strides[i];
        }
        oss << "])";
        return oss.str();
    }
};

int main() {
    Tensor t({1, 2, 3, 4, 5, 6}, {2, 3});
    std::cout << t.repr()         << "\n";
    std::cout << "t[0,0] = " << t[{0, 0}] << "\n";  // 1
    std::cout << "t[1,2] = " << t[{1, 2}] << "\n";  // 6
    std::cout << "numel  = " << t.numel()  << "\n";  // 6
    return 0;
}
