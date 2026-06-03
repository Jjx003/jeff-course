"""Simulate a tiny continuous batching decode scheduler."""

REQUESTS = [
    {"id": "A", "arrival": 0, "tokens": 3},
    {"id": "B", "arrival": 0, "tokens": 1},
    {"id": "C", "arrival": 1, "tokens": 2},
    {"id": "D", "arrival": 2, "tokens": 2},
]

MAX_ACTIVE = 2


def simulate(requests, max_active):
    # TODO: return (timeline, completed), where timeline is a list of
    # (tick, active_ids_before_generation) and completed maps id -> finish tick.
    return ...


def main():
    timeline, completed = simulate(REQUESTS, MAX_ACTIVE)
    for tick, active in timeline:
        print(f"t={tick}: active={','.join(active)}")
    print("completed:", " ".join(f"{key}:{completed[key]}" for key in sorted(completed)))


if __name__ == "__main__":
    main()

