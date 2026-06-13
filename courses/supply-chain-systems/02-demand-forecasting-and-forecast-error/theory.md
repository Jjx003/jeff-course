# Forecasts Serve Decisions

A forecast should be judged against the decision it supports. A daily warehouse labor plan needs a different horizon and granularity than a six-month raw-material commitment.

## Error measures

Let actual demand be $A_t$ and forecast demand be $F_t$.

The error is:

$$
e_t = A_t - F_t
$$

Positive error means demand exceeded the forecast. Negative error means the forecast was too high.

Common metrics:

| Metric | Formula | Use |
|---|---|---|
| Mean error | average of $e_t$ | detects bias |
| MAE | average of $|e_t|$ | interpretable absolute error |
| RMSE | square root of average $e_t^2$ | penalizes large misses |
| MAPE | average of $|e_t/A_t|$ | percentage error, unstable near zero |

Bias is especially dangerous. A noisy but unbiased forecast can be buffered. A consistently biased forecast quietly shifts the whole operating system.

## Horizon matters

Forecast error usually grows with horizon. The relevant horizon is the time between committing resources and receiving usable output. If supplier lead time is 12 weeks, a one-week forecast accuracy dashboard may be comforting but insufficient.

## Aggregate forecasts are easier

Forecasting a product family is usually easier than forecasting a single SKU-location. This creates a planning tension: aggregate forecasts are more accurate, but operations need SKU-level decisions.

Hierarchical forecasting tries to reconcile these levels:

- total category demand
- product family demand
- SKU demand
- SKU-location demand

## Intermittent demand

Spare parts, specialty chemicals, and low-volume industrial items often have many zero-demand periods. Ordinary percentage error can become meaningless. In these cases, planners care about probability of demand during lead time and the cost of not having the item.

## Forecast error is an economic variable

An error distribution becomes operational when paired with decisions. If underforecasting costs lost sales and overforecasting costs markdowns, the best decision may intentionally target a service level above or below the median forecast.
