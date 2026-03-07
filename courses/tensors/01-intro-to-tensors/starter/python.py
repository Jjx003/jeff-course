import math
from typing import Tuple, List


class Tensor:
    def __init__(self, data: List[float], shape: Tuple[int, ...]):
        """
        Args:
            data:  flat list of numbers in row-major (C) order
            shape: tuple of dimension sizes, e.g. (2, 3)
        """
        assert len(data) == math.prod(shape), (
            f"Data length {len(data)} does not match shape {shape} "
            f"(expected {math.prod(shape)} elements)"
        )
        self.data = list(data)
        self.shape = shape
        self.strides = self._compute_strides(shape)

    def _compute_strides(self, shape: Tuple[int, ...]) -> Tuple[int, ...]:
        # TODO: compute C-contiguous strides for the given shape.
        # Hint: start from the last dimension (stride = 1) and work backwards.
        raise NotImplementedError

    def __getitem__(self, indices):
        """Support indexing like t[1, 2] or t[0, 0, 3]."""
        if isinstance(indices, int):
            indices = (indices,)
        # TODO: compute the flat offset and return self.data[offset]
        raise NotImplementedError

    def numel(self) -> int:
        """Return the total number of elements."""
        # TODO
        raise NotImplementedError

    def __repr__(self) -> str:
        preview = self.data[:6]
        suffix = "..." if len(self.data) > 6 else ""
        return f"Tensor(shape={self.shape}, strides={self.strides}, data=[{', '.join(map(str, preview))}{suffix}])"


# ── Quick smoke test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    t = Tensor([1, 2, 3, 4, 5, 6], (2, 3))
    print(t)
    print("shape  :", t.shape)    # (2, 3)
    print("strides:", t.strides)  # (3, 1)
    print("t[0,0] :", t[0, 0])   # 1
    print("t[1,2] :", t[1, 2])   # 6
    print("numel  :", t.numel())  # 6
