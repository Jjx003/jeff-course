"""Compare supply-chain disruption mitigations."""


SCENARIOS = [
    {"name": "port closure", "probability": 0.18, "impact_usd": 1_900_000, "recovery_days": 21},
    {"name": "supplier quality escape", "probability": 0.10, "impact_usd": 2_700_000, "recovery_days": 35},
    {"name": "regional power outage", "probability": 0.06, "impact_usd": 5_500_000, "recovery_days": 50},
]

MITIGATIONS = [
    {"name": "alternate port routing", "cost_usd": 120_000, "risk_reduction": 0.45, "applies_to": "port closure"},
    {"name": "dual source critical component", "cost_usd": 380_000, "risk_reduction": 0.55, "applies_to": "supplier quality escape"},
    {"name": "backup generation and cold inventory", "cost_usd": 520_000, "risk_reduction": 0.35, "applies_to": "regional power outage"},
]


def expected_loss(scenario):
    # TODO: probability times impact.
    return ...


def residual_loss(scenario, mitigation):
    # TODO: reduce expected loss by mitigation risk_reduction when it applies.
    return ...


def mitigation_value(scenario, mitigation):
    # TODO: baseline loss minus residual loss minus annual mitigation cost.
    return ...


def main():
    print("=== baseline expected annual losses ===")
    for scenario in SCENARIOS:
        print(f"{scenario['name']}: ${expected_loss(scenario):,.0f}")

    print("=== mitigation net values ===")
    for mitigation in MITIGATIONS:
        scenario = next(s for s in SCENARIOS if s["name"] == mitigation["applies_to"])
        value = mitigation_value(scenario, mitigation)
        print(f"{mitigation['name']}: ${value:,.0f}")


if __name__ == "__main__":
    main()
