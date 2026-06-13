# The Critical Fractile

Suppose you must choose an order quantity $Q$ before demand $D$ is known.

If you order too little, each missing unit creates underage cost $C_u$. This may include lost margin, expediting, penalties, or customer churn.

If you order too much, each leftover unit creates overage cost $C_o$. This may include markdowns, obsolescence, holding cost, disposal, or tied capital.

The optimal service fractile is:

$$
\frac{C_u}{C_u + C_o}
$$

This is the probability target for demand being less than or equal to your order quantity.

## Example

If a stockout costs USD 30 per unit and excess costs USD 10 per unit, the critical fractile is:

$$
\frac{30}{30+10}=0.75
$$

You should choose the 75th percentile of the demand distribution, not the mean.

## Cycle service versus fill rate

Two service metrics are often confused:

- Cycle service level: probability of no stockout in a replenishment cycle.
- Fill rate: fraction of demand fulfilled immediately from stock.

A system can have a modest cycle service level but high fill rate if stockouts are shallow. It can also have high cycle service but poor fill rate if rare stockouts are severe.

## Safety stock

Safety stock protects against demand and lead-time variability. A common approximation is:

$$
SS = z \sigma_{LTD}
$$

where $\sigma_{LTD}$ is the standard deviation of demand during lead time and $z$ is the standard-normal service factor.

The reorder point is:

$$
ROP = \mu_{LTD} + SS
$$

where $\mu_{LTD}$ is mean demand during lead time.

## Managerial interpretation

The model does not remove judgment. It forces judgment into explicit costs. If the team cannot say what shortages and leftovers cost, the service-level target is probably folklore.
