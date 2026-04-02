"""
Matrix Multiplication — Solution

Implements matmul(A, B) for two 2-D Tensors using the naive triple loop.
No NumPy allowed; all arithmetic is done via the flat data buffer through
the Tensor indexing helpers.
"""
import math
from typing import List, Tuple


class Tensor:
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


# ── Solution ─────────────────────────────────────────────────────────────────

def matmul(A: Tensor, B: Tensor) -> Tensor:
    """
    Multiply two 2-D tensors A (m x k) and B (k x n) → C (m x n).

    C[i, j] = sum over p of A[i, p] * B[p, j]

    Args:
        A: Tensor of shape (m, k)
        B: Tensor of shape (k, n)

    Returns:
        C: Tensor of shape (m, n)

    Raises:
        ValueError: if A.shape[1] != B.shape[0] (inner dimensions must match)
    """
    if len(A.shape) != 2 or len(B.shape) != 2:
        raise ValueError(
            f"matmul requires 2-D tensors, got shapes {A.shape} and {B.shape}"
        )

    m, k = A.shape
    k2, n = B.shape

    if k != k2:
        raise ValueError(
            f"Inner dimensions must match: A is ({m}, {k}), B is ({k2}, {n})"
        )

    # Allocate output filled with zeros (use int 0 so integer inputs stay integer)
    C = Tensor([0] * (m * n), (m, n))

    # Naive triple loop: O(m * n * k)
    for i in range(m):
        for j in range(n):
            acc = 0
            for p in range(k):
                acc += A[i, p] * B[p, j]
            C[i, j] = acc

    return C


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
