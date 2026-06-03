## Build a tiny fab economics model

You are given a simplified manufacturing model for a logic chip. Your task is
to estimate how many sellable dies a fab can produce per month.

Implement four functions:

1. `die_per_wafer(wafer_diameter_mm, die_area_mm2)` estimates how many
   rectangular dies fit on a circular wafer.
2. `poisson_yield(die_area_mm2, defect_density_per_cm2)` estimates the
   probability that a die has zero fatal random defects.
3. `good_die_per_month(wafers_per_month, wafer_diameter_mm, die_area_mm2,
   defect_density_per_cm2)` combines wafer capacity, die count, and yield.
4. `bottleneck_capacity(step_capacities)` returns the step name and wafer-per-
   month capacity of the limiting process step.

Use the formulas in the theory tab. The starter file includes deterministic
examples; your output should match the expected output exactly when rounded by
the provided `main()`.

## Constraints

- Use Python's standard library only.
- Treat `die_area_mm2` and `wafer_diameter_mm` as positive numbers.
- Treat defect density as defects per square centimeter.
- Preserve the public function names and the printed format in `main()`.

## Why this matters

A large AI accelerator die can be reticle-limited, yield-sensitive, and
packaging-constrained at the same time. This exercise is intentionally small,
but it gives you the habit of separating wafer capacity, die size, yield, and
bottlenecks instead of compressing everything into one vague phrase like
"supply."
