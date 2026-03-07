"""
Broadcasting

Implement broadcast_shapes() and broadcast_add().
"""
import math
import itertools
from typing import Tuple, List


class Tensor:
    """Reuse from problem 1 (full version with __setitem__)."""

    def __init__(self, data: List[float], shape: Tuple[int, ...]):
        assert len(data) == math.prod(shape) if shape else len(data) == 1
        self.data = list(data)
        self.shape = shape
        self.strides = self._compute_strides(shape)

    def _compute_strides(self, shape):
        if not shape:
            return ()
        strides = [1] * len(shape)
        for i in range(len(shape) - 2, -1, -1):
            strides[i] = strides[i + 1] * shape[i + 1]
        return tuple(strides)

    def _offset(self, indices):
        return sum(i * s for i, s in zip(indices, self.strides))

    def __getitem__(self, indices):
        if isinstance(indices, int):
            indices = (indices,)
        return self.data[self._offset(indices)]

    def __setitem__(self, indices, value):
        if isinstance(indices, int):
            indices = (indices,)
        self.data[self._offset(indices)] = value

    def numel(self):
        return math.prod(self.shape)

    def __repr__(self):
        return f"Tensor(shape={self.shape})"


# ── Your implementation ──────────────────────────────────────────────────────

def broadcast_shapes(shape_a: Tuple[int, ...], shape_b: Tuple[int, ...]) -> Tuple[int, ...]:
    """
    Compute the output shape of broadcasting shape_a with shape_b.

    Raises ValueError for incompatible shapes.
    """
    # TODO: implement broadcasting rules
    raise NotImplementedError


def broadcast_add(A: Tensor, B: Tensor) -> Tensor:
    """
    Add A and B element-wise with broadcasting.

    Returns a new Tensor with the broadcast shape.
    """
    # TODO:
    # 1. Compute out_shape = broadcast_shapes(A.shape, B.shape)
    # 2. Pad A.shape and B.shape with leading 1s to match ndim
    # 3. Iterate over all indices in out_shape
    # 4. Clamp each index into A and B, read values, write sum to C
    raise NotImplementedError


# ── Smoke tests ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test 1: scalar broadcast
    a = Tensor([1, 2, 3], (3,))
    b = Tensor([10], (1,))
    c = broadcast_add(a, b)
    print("Test 1:", [c[i] for i in range(3)])  # [11, 12, 13]

    # Test 2: row + column → matrix
    row = Tensor([1, 2, 3], (1, 3))
    col = Tensor([10, 20], (2, 1))
    out = broadcast_add(row, col)
    print("Test 2 shape:", out.shape)  # (2, 3)
    print("Test 2 data:", out.data)    # [11, 12, 13, 21, 22, 23]

    # Test 3: incompatible shapes
    try:
        broadcast_add(Tensor([1, 2, 3], (3,)), Tensor([1, 2], (2,)))
        print("Test 3: FAILED (should have raised)")
    except ValueError as e:
        print("Test 3: OK (raised ValueError)")
