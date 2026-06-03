"""Simulate a tiny continuous batching decode scheduler."""

REQUESTS = [
    {"id": "A", "arrival": 0, "tokens": 3},
    {"id": "B", "arrival": 0, "tokens": 1},
    {"id": "C", "arrival": 1, "tokens": 2},
    {"id": "D", "arrival": 2, "tokens": 2},
]

MAX_ACTIVE = 2


def simulate(requests, max_active):
    waiting = [dict(request, remaining=request["tokens"]) for request in requests]
    active = []
    completed = {}
    timeline = []
    tick = 0

    while waiting or active:
        while len(active) < max_active:
            ready_index = next(
                (i for i, request in enumerate(waiting) if request["arrival"] <= tick),
                None,
            )
            if ready_index is None:
                break
            active.append(waiting.pop(ready_index))

        if not active:
            tick += 1
            continue

        timeline.append((tick, [request["id"] for request in active]))

        for request in active:
            request["remaining"] -= 1

        still_active = []
        for request in active:
            if request["remaining"] == 0:
                completed[request["id"]] = tick + 1
            else:
                still_active.append(request)
        active = still_active
        tick += 1

    return timeline, completed


def main():
    timeline, completed = simulate(REQUESTS, MAX_ACTIVE)
    for tick, active in timeline:
        print(f"t={tick}: active={','.join(active)}")
    print("completed:", " ".join(f"{key}:{completed[key]}" for key in sorted(completed)))


if __name__ == "__main__":
    main()

