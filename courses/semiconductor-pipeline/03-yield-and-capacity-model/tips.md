## Hints

Implement `die_per_wafer` with `math.pi`, `math.sqrt`, and `math.floor`. The
formula returns a floating-point estimate; the function should return a whole
number of dies.

For `poisson_yield`, remember that defect density is per cm^2 but die area is
given in mm^2. Divide by 100 before multiplying by the defect density.

For `good_die_per_month`, call your earlier functions instead of repeating the
formulas.

For `bottleneck_capacity`, dictionaries have `.items()`. The built-in `min()`
can choose the pair with the lowest capacity if you pass a suitable `key`.

## Going deeper

After you solve the exercise, try changing the die area from `120` to `800`.
The dies-per-wafer and yield both move against you, which is one reason very
large accelerators are so sensitive to process maturity and packaging strategy.
