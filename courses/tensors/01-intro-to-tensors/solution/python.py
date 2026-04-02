import math
from typing import Tuple, List


class Tensor:
    def __init__(self, data: List[float], shape: Tuple[int, ...]):
        assert len(data) == math.prod(shape), (
            f"Data length {len(data)} does not match shape {shape} "
            f"(expected {math.prod(shape)} elements)"
        )
        self.data = list(data)
        self.shape = shape
        self.strides = self._compute_strides(shape)

    def _compute_strides(self, shape: Tuple[int, ...]) -> Tuple[int, ...]:
        strides = []
        stride = 1
        for dim in reversed(shape):
            strides.append(stride)
            stride *= dim
        return tuple(reversed(strides))

    def __getitem__(self, indices):
        if isinstance(indices, int):
            indices = (indices,)
        offset = sum(i * s for i, s in zip(indices, self.strides))
        return self.data[offset]

    def numel(self) -> int:
        return math.prod(self.shape)

    def __repr__(self) -> str:
        preview = self.data[:6]
        suffix = "..." if len(self.data) > 6 else ""
        return f"Tensor(shape={self.shape}, strides={self.strides}, data=[{', '.join(map(str, preview))}{suffix}])"


if __name__ == "__main__":
    t = Tensor([1, 2, 3, 4, 5, 6], (2, 3))
    print(t)
    print("shape  :", t.shape)
    print("strides:", t.strides)
    print("t[0,0] :", t[0, 0])
    print("t[1,2] :", t[1, 2])
    print("numel  :", t.numel())
