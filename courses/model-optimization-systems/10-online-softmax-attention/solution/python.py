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
    max_score = max(scores)
    weights = [math.exp(score - max_score) for score in scores]
    denom = sum(weights)
    return [
        sum(weight * value[col] for weight, value in zip(weights, values)) / denom
        for col in range(len(values[0]))
    ]


def online_attention(scores, values, block_size):
    running_max = -math.inf
    running_denom = 0.0
    numerator = [0.0 for _ in values[0]]

    for start in range(0, len(scores), block_size):
        block_scores = scores[start:start + block_size]
        block_values = values[start:start + block_size]
        block_max = max(block_scores)
        new_max = max(running_max, block_max)

        old_scale = math.exp(running_max - new_max) if running_denom else 0.0
        block_weights = [math.exp(score - new_max) for score in block_scores]

        numerator = [x * old_scale for x in numerator]
        for weight, value in zip(block_weights, block_values):
            for col in range(len(numerator)):
                numerator[col] += weight * value[col]

        running_denom = running_denom * old_scale + sum(block_weights)
        running_max = new_max

    return [x / running_denom for x in numerator]


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

