# Tips & Notes

## Structure

Reuse your `Tensor` class from problem 1. If you haven't finished it, here is
a minimal version to unblock yourself:

```python
class Tensor:
    def __init__(self, data, shape):
        self.data = list(data)
        self.shape = shape
        n = shape[-1] if len(shape) > 1 else 1
        self.strides = (n, 1) if len(shape) == 2 else (1,)

    def __getitem__(self, idx):
        i, j = idx
        return self.data[i * self.strides[0] + j * self.strides[1]]

    def __setitem__(self, idx, val):
        i, j = idx
        self.data[i * self.strides[0] + j * self.strides[1]] = val
```

## Output Tensor

Allocate the output as a flat list of zeros, then build the `Tensor` at the end:

```python
result_data = [0.0] * (m * n)
C = Tensor(result_data, (m, n))
```

Then fill via `C[i, j] = ...` — you may need to add `__setitem__` to your Tensor.

## Validation

```python
A = Tensor([1,0, 0,1], (2,2))   # identity
B = Tensor([5,6, 7,8], (2,2))
C = matmul(A, B)
assert C[0,0] == 5 and C[1,1] == 8, "Identity matmul failed"
```

## Loop Order Experiment

Time both ijk and ikj for a 256×256 matrix:

```python
import time

def bench(fn, A, B, label):
    t0 = time.perf_counter()
    fn(A, B)
    t1 = time.perf_counter()
    print(f"{label}: {(t1-t0)*1000:.1f} ms")
```

You should see ikj outperform ijk by 2–5× for large matrices.
