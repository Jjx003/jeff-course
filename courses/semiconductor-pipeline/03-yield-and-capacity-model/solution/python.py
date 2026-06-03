from __future__ import annotations

from math import exp, floor, pi, sqrt


def die_per_wafer(wafer_diameter_mm: float, die_area_mm2: float) -> int:
    """Estimate complete rectangular dies on a circular wafer."""
    gross = (pi * wafer_diameter_mm**2) / (4.0 * die_area_mm2)
    edge_loss = (pi * wafer_diameter_mm) / sqrt(2.0 * die_area_mm2)
    return floor(gross - edge_loss)


def poisson_yield(die_area_mm2: float, defect_density_per_cm2: float) -> float:
    """Return the probability that a die has zero fatal random defects."""
    die_area_cm2 = die_area_mm2 / 100.0
    expected_defects = die_area_cm2 * defect_density_per_cm2
    return exp(-expected_defects)


def good_die_per_month(
    wafers_per_month: int,
    wafer_diameter_mm: float,
    die_area_mm2: float,
    defect_density_per_cm2: float,
) -> int:
    """Estimate good dies per month after random-defect yield loss."""
    dies = die_per_wafer(wafer_diameter_mm, die_area_mm2)
    yld = poisson_yield(die_area_mm2, defect_density_per_cm2)
    return floor(wafers_per_month * dies * yld)


def bottleneck_capacity(step_capacities: dict[str, int]) -> tuple[str, int]:
    """Return the process step with the lowest wafer-per-month capacity."""
    return min(step_capacities.items(), key=lambda item: item[1])


def main() -> None:
    scenarios = [
        ("edge_ai_soc", 300, 120, 0.08, 45_000),
        ("datacenter_gpu", 300, 820, 0.05, 45_000),
        ("mature_mcu", 200, 24, 0.12, 70_000),
    ]

    for name, diameter, area, defects, wafers in scenarios:
        dpw = die_per_wafer(diameter, area)
        yld = poisson_yield(area, defects)
        good = good_die_per_month(wafers, diameter, area, defects)
        print(f"{name}: dies/wafer={dpw}, yield={yld:.3f}, good/month={good}")

    capacities = {
        "lithography": 52_000,
        "etch": 61_000,
        "deposition": 58_000,
        "cmp": 49_000,
        "inspection": 54_000,
    }
    step, capacity = bottleneck_capacity(capacities)
    print(f"bottleneck: {step} at {capacity} wafers/month")


if __name__ == "__main__":
    main()
