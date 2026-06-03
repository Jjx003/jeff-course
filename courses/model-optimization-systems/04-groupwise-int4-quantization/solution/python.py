"""Groupwise symmetric INT4 quantization."""

WEIGHTS = [-1.2, -0.8, -0.1, 0.0, 0.4, 1.3, 2.0, -2.2, 0.05, -0.07, 3.1, -3.4]
GROUP_SIZE = 4


def chunks(values, size):
    for i in range(0, len(values), size):
        yield values[i:i + size]


def quantize_group(group):
    max_abs = max(abs(x) for x in group)
    scale = max_abs / 7 if max_abs else 1.0
    q_values = []
    for value in group:
        q = round(value / scale)
        q_values.append(max(-7, min(7, q)))
    return scale, q_values


def dequantize_group(q_values, scale):
    return [q * scale for q in q_values]


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

