"""
Matrix Multiplication

Implement matmul(A, B) for two 2-D Tensors.
Reuse or re-paste your Tensor class from problem 1.
"""
import math
from typing import List, Tuple


class Tensor:
    """Copy your implementation from problem 1, or use this placeholder."""

    def __init__(self, data: List[float], shape: Tuple[int, ...]):
        assert len(data) == math.prod(shape)
        self.data = list(data)
        self.shape = shape
        self.strides = self._compute_strides(shape)

    def _compute_strides(self, shape):
        strides = [1] * len(shape)
        for i in range(len(shape) - 2, -1, -1):
            strides[i] = strides[i + 1] * shape[i + 1]
        return tuple(strides)

    def __getitem__(self, indices):
        if isinstance(indices, int):
            indices = (indices,)
        offset = sum(i * s for i, s in zip(indices, self.strides))
        return self.data[offset]

    def __setitem__(self, indices, value):
        if isinstance(indices, int):
            indices = (indices,)
        offset = sum(i * s for i, s in zip(indices, self.strides))
        self.data[offset] = value

    def numel(self):
        return math.prod(self.shape)

    def __repr__(self):
        return f"Tensor(shape={self.shape})"


# ── Your implementation ──────────────────────────────────────────────────────

def matmul(A: Tensor, B: Tensor) -> Tensor:
    """
    Multiply two 2-D tensors.

    Args:
        A: shape (m, k)
        B: shape (k, n)

    Returns:
        C: shape (m, n)

    Raises:
        ValueError: if A.shape[1] != B.shape[0]
    """
    # TODO: validate shapes
    # TODO: allocate output tensor C of shape (m, n) filled with zeros
    # TODO: implement the triple loop
    raise NotImplementedError


# ── Smoke test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    A = Tensor([1, 2, 3, 4, 5, 6], (2, 3))
    B = Tensor([7, 8, 9, 10, 11, 12], (3, 2))

    C = matmul(A, B)
    print("C shape:", C.shape)   # (2, 2)
    print("C[0,0]:", C[0, 0])   # 58
    print("C[0,1]:", C[0, 1])   # 64
    print("C[1,0]:", C[1, 0])   # 139
    print("C[1,1]:", C[1, 1])   # 154
