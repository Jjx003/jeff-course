"""Estimate speculative decoding speedups."""

SCENARIOS = [
    ("weak draft", 4, 0.55, 0.08),
    ("solid draft", 4, 0.75, 0.08),
    ("long draft", 8, 0.75, 0.08),
    ("expensive draft", 4, 0.75, 0.25),
]


def expected_committed(draft_len, acceptance):
    # TODO: return 1 + sum(acceptance ** i for i in 1..draft_len).
    return ...


def speedup(draft_len, acceptance, draft_cost):
    # TODO: committed tokens divided by target-plus-draft cost.
    return ...


def main():
    for name, draft_len, acceptance, draft_cost in SCENARIOS:
        committed = expected_committed(draft_len, acceptance)
        gain = speedup(draft_len, acceptance, draft_cost)
        print(f"{name}: committed={committed:.2f} speedup={gain:.2f}x")


if __name__ == "__main__":
    main()

