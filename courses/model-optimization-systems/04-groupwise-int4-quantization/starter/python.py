"""Groupwise symmetric INT4 quantization."""

WEIGHTS = [-1.2, -0.8, -0.1, 0.0, 0.4, 1.3, 2.0, -2.2, 0.05, -0.07, 3.1, -3.4]
GROUP_SIZE = 4


def chunks(values, size):
    for i in range(0, len(values), size):
        yield values[i:i + size]


def quantize_group(group):
    # TODO: compute scale = max(abs(x)) / 7, using 1.0 for an all-zero group.
    # TODO: return the scale and a list of clipped integer q values.
    return ...


def dequantize_group(q_values, scale):
    # TODO: return q * scale for each q.
    return ...


def main():
    scales = []
    q_all = []
    restored = []

    for group in chunks(WEIGHTS, GROUP_SIZE):
        scale, q_values = quantize_group(group)
        scales.append(scale)
        q_all.extend(q_values)
        restored.extend(dequantize_group(q_values, scale))

    mae = sum(abs(a - b) for a, b in zip(WEIGHTS, restored)) / len(WEIGHTS)

    print("scales:", [round(s, 6) for s in scales])
    print("q:", q_all)
    print("restored:", [round(x, 3) for x in restored])
    print(f"mae: {mae:.4f}")


if __name__ == "__main__":
    main()

