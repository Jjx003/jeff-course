# Scenario Models

A scenario model combines probability, impact, recovery time, and mitigation cost.

Expected annual loss can be approximated as:

$$
E[L] = p \times impact
$$

where impact may include lost margin, expediting, penalties, scrap, overtime, and customer churn.

## Recovery metrics

Two useful measures are:

- time to survive: how long the system can continue before customer impact
- time to recover: how long until normal service is restored

If time to survive is shorter than time to recover, the gap creates customer impact unless another mitigation is available.

## Mitigation value

A mitigation has value if it reduces expected loss by more than its annual cost, while also fitting strategy and feasibility constraints.

Not all risk reduction is visible in expected value. A low-probability, high-severity event may be worth mitigating because it threatens the enterprise, not because the simple expected value is large.
