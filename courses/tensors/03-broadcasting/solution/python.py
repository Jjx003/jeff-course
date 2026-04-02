"""
Broadcasting — Solution

Implements broadcast_shapes() and broadcast_add() following NumPy rules.
"""
import math
import itertools
from typing import Tuple, List


class Tensor:
    """Full Tensor class with shape, strides, and element access."""

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


# ── Implementation ────────────────────────────────────────────────────────────

def broadcast_shapes(shape_a: Tuple[int, ...], shape_b: Tuple[int, ...]) -> Tuple[int, ...]:
    """
    Compute the output shape of broadcasting shape_a with shape_b.

    Shapes are aligned right-to-left. For each dimension pair:
      - equal sizes → keep that size
      - one size is 1 → use the other size
      - both > 1 and unequal → raise ValueError
    Missing leading dimensions are treated as size 1.

    Raises ValueError for incompatible shapes.
    """
    # Pad the shorter shape with leading 1s so both have the same length.
    ndim = max(len(shape_a), len(shape_b))
    pa = (1,) * (ndim - len(shape_a)) + tuple(shape_a)
    pb = (1,) * (ndim - len(shape_b)) + tuple(shape_b)

    out = []
    for a, b in zip(pa, pb):
        if a == b:
            out.append(a)
        elif a == 1:
            out.append(b)
        elif b == 1:
            out.append(a)
        else:
            raise ValueError(
                f"Shapes {shape_a} and {shape_b} are not broadcastable: "
                f"dimension sizes {a} and {b} are incompatible."
            )
    return tuple(out)


def broadcast_add(A: Tensor, B: Tensor) -> Tensor:
    """
    Add A and B element-wise with broadcasting.

    Returns a new Tensor with the broadcast shape.
    """
    out_shape = broadcast_shapes(A.shape, B.shape)
    ndim = len(out_shape)

    # Pad both shapes with leading 1s to match the output rank.
    pa = (1,) * (ndim - len(A.shape)) + tuple(A.shape)
    pb = (1,) * (ndim - len(B.shape)) + tuple(B.shape)

    # Allocate output data buffer.
    out_data = [0.0] * math.prod(out_shape)
    C = Tensor(out_data, out_shape)

    # Iterate over every multi-index in the output shape.
    for out_idx in itertools.product(*[range(s) for s in out_shape]):
        # Map output index to input indices by clamping broadcast (size-1) dims to 0.
        a_idx = tuple(0 if pa[d] == 1 else out_idx[d] for d in range(ndim))
        b_idx = tuple(0 if pb[d] == 1 else out_idx[d] for d in range(ndim))

        C[out_idx] = A[a_idx] + B[b_idx]

    return C


# ── Smoke tests ───────────────────────────────────────────────────────────────
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
