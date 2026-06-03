"""One-row attention with naive softmax and online softmax."""

import math

SCORES = [1.0, 2.0, -1.0, 0.5]
VALUES = [
    [1.0, 0.0],
    [0.0, 2.0],
    [3.0, 1.0],
    [-1.0, 1.0],
]


def naive_attention(scores, values):
    # TODO: stable softmax over all scores, then weighted sum of values.
    return ...


def online_attention(scores, values, block_size):
    # TODO: stream blocks and maintain running max, denominator, and numerator.
    return ...


def max_abs_diff(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


def main():
    naive = naive_attention(SCORES, VALUES)
    online = online_attention(SCORES, VALUES, block_size=2)
    print("naive:", [round(x, 6) for x in naive])
    print("online:", [round(x, 6) for x in online])
    print(f"max diff: {max_abs_diff(naive, online):.8f}")


if __name__ == "__main__":
    main()

