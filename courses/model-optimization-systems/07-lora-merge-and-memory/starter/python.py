"""Merge a tiny LoRA adapter into a base matrix."""

W = [
    [1.0, -2.0, 0.5],
    [0.0, 1.5, -1.0],
]

A = [
    [0.2, -0.1, 0.0],
    [0.0, 0.3, -0.2],
]

B = [
    [1.0, -0.5],
    [0.25, 0.75],
]

ALPHA = 4


def matmul(left, right):
    # TODO: multiply two nested-list matrices.
    return ...


def add(left, right):
    # TODO: elementwise matrix addition.
    return ...


def scale_matrix(matrix, scale):
    # TODO: multiply every value by scale.
    return ...


def rounded(matrix):
    return [[round(x, 3) for x in row] for row in matrix]


def main():
    rank = len(A)
    scale = ALPHA / rank
    dense_params = len(W) * len(W[0])
    adapter_params = len(A) * len(A[0]) + len(B) * len(B[0])

    # TODO: compute delta = scale * B @ A and merged = W + delta.

    print(f"scale: {scale:.1f}")
    print(f"dense params: {dense_params}")
    print(f"adapter params: {adapter_params}")
    print(f"adapter percent: {adapter_params / dense_params * 100:.1f}%")
    print("delta:", rounded(delta))
    print("merged:", rounded(merged))


if __name__ == "__main__":
    main()

