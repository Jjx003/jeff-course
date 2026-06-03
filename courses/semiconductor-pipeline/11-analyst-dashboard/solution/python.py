"""
Rank semiconductor pipeline bottlenecks from a small embedded dataset.
"""

PIPELINE_ITEMS = [
    {
        "name": "Advanced packaging",
        "capacity_units": 72,
        "demand_units": 96,
        "backlog_units": 180,
        "monthly_clear_rate": 45,
        "strategic_weight": 5.0,
        "note": "interposer and substrate capacity gate AI accelerators",
    },
    {
        "name": "HBM stacks",
        "capacity_units": 90,
        "demand_units": 132,
        "backlog_units": 210,
        "monthly_clear_rate": 42,
        "strategic_weight": 4.8,
        "note": "memory allocation limits module shipments",
    },
    {
        "name": "DUV immersion tools",
        "capacity_units": 45,
        "demand_units": 48,
        "backlog_units": 72,
        "monthly_clear_rate": 18,
        "strategic_weight": 4.4,
        "note": "critical for mature-node and multipatterning expansion",
    },
    {
        "name": "Optical transceivers",
        "capacity_units": 150,
        "demand_units": 168,
        "backlog_units": 120,
        "monthly_clear_rate": 60,
        "strategic_weight": 3.9,
        "note": "cluster scale-out needs high-speed links",
    },
    {
        "name": "Data-center power",
        "capacity_units": 65,
        "demand_units": 91,
        "backlog_units": 156,
        "monthly_clear_rate": 39,
        "strategic_weight": 4.6,
        "note": "rack deployment waits on power and cooling readiness",
    },
]


def utilization(item):
    """Return demand divided by effective capacity."""
    return item["demand_units"] / item["capacity_units"]


def months_to_clear_backlog(item):
    """Return backlog divided by monthly clearance rate."""
    return item["backlog_units"] / item["monthly_clear_rate"]


def constraint_score(item):
    """Return the weighted bottleneck score for one item."""
    return (
        0.55 * utilization(item)
        + 0.30 * months_to_clear_backlog(item)
        + 0.15 * item["strategic_weight"]
    )


def summarize_top_constraints(items, top_n=3):
    """Return formatted summary lines for the top constraints."""
    ranked = sorted(
        items,
        key=lambda item: (-constraint_score(item), -utilization(item), item["name"]),
    )

    lines = []
    for rank, item in enumerate(ranked[:top_n], start=1):
        lines.append(
            f"{rank}. {item['name']} | "
            f"util={utilization(item):.2f}x | "
            f"backlog={months_to_clear_backlog(item):.2f} mo | "
            f"score={constraint_score(item):.2f} | "
            f"note={item['note']}"
        )
    return lines


def main():
    print("Semiconductor pipeline constraint dashboard")
    print("-------------------------------------------")
    for line in summarize_top_constraints(PIPELINE_ITEMS):
        print(line)

    print()
    for name in ["HBM stacks", "Optical transceivers"]:
        item = next(row for row in PIPELINE_ITEMS if row["name"] == name)
        print(
            f"{name}: utilization={utilization(item):.2f}x, "
            f"months_to_clear={months_to_clear_backlog(item):.2f}"
        )


if __name__ == "__main__":
    main()
