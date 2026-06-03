## Solution walkthrough

The key step is converting pH and pKa into the protonated fraction:

$$
f_\mathrm{prot} = \frac{1}{1 + 10^{\mathrm{pH} - \mathrm{p}K_a}}
$$

Once you have that value, acids and bases differ only in how protonation maps
to charge.

For an acid, the protonated form is neutral and the deprotonated form is
negative:

```python
return -(1.0 - fraction)
```

For a base, the protonated form is positive and the deprotonated form is
neutral:

```python
return fraction
```

`net_charge` then just looks up each group key and sums the expected charges.
The output is fractional because it represents an ensemble average, not a
single molecule frozen in one protonation state.
