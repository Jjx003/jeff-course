# Theory: Ranking Bottlenecks

A bottleneck ranking is a compact model. It is useful because it forces assumptions into the open.

## Utilization

Utilization compares demand with effective capacity:

$$
\text{utilization} = \frac{\text{demand}}{\text{capacity}}
$$

Values above 1.0 mean demand exceeds current capacity. In real semiconductor work, "capacity" should already include yield, uptime, product mix, and qualification constraints. Nameplate capacity alone can mislead.

## Backlog clearance

Backlog clearance estimates how long a queue would take to clear at the current monthly rate:

$$
\text{months to clear} = \frac{\text{backlog}}{\text{monthly clear rate}}
$$

This is a rough queueing proxy. It ignores new incoming orders, but it is still helpful for comparing layers.

## Constraint score

The score in this exercise combines three ideas:

$$
\text{score} =
0.55u + 0.30b + 0.15s
$$

where:

- $u$ is utilization.
- $b$ is months to clear backlog.
- $s$ is strategic weight.

The weights are not universal. In real work, you would test sensitivity: does the ranking change if backlog matters more, or if strategic weight is lower?

## Why qualitative notes stay in the output

Dashboards can create false precision. A score of 3.18 is not magic. The note reminds the analyst why the row matters: HBM allocation, advanced packaging, optics, power, cooling, mature-node exposure, or policy sensitivity. Good analysis keeps numbers and narrative tied together.
