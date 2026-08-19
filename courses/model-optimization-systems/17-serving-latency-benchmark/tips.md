# Hints

## Part 1

- `Fraction(str(q))` — stringify first. `Fraction(99.9)` builds the exact
  binary float 99.9000000000000056..., which reintroduces the bug the
  Fraction was supposed to kill.
- Clamp the rank to `[1, n]` before indexing; q=0 would otherwise index -1.
- Expected: `p50=500 p90=900 p99=990 p99.9=999` on `1..1000`. If you get
  `p99.9=1000`, you computed the rank in floats.

## Part 2

- The simulator needs no heap and no event objects: arrivals are already in
  order, so a running `now` and a running `server_free` are the whole state.
- The wait excludes the request's own service. If your ratios sit near 1.5,
  you added it.
- Do not re-seed inside the loop; each rho gets one `random.Random(...)`
  built from the constants in the starter.

## Part 3

- `lam = rho / mean_service` keeps everything in milliseconds; the printed
  req/s column multiplies by 1000.
- `E[S^2]` comes from the *sampled* services, not the analytic distribution
  — that is deliberate, the prediction should use what the benchmark saw.
- TTFT here is wait + prefill only. The first token is produced after
  prefill; the remaining tokens are ITL, which this single-server model
  makes constant (a real engine's ITL varies with batch interference —
  module 12 is where that comes from).

## Part 4

- Push `(finish + think, client)` — the *next send* — after serving, not
  before. If the closed loop reports the same p99 as the open loop, each
  client is probably sending without waiting for its completion.
- Think times are drawn per send with `rng.expovariate(1.0 / think_mean)`;
  drawing one think time per client and reusing it changes the output.
- Draw the service *when the request starts* (`sample_service(rng)` inside
  the loop), matching the reference RNG consumption order. Pre-generating
  services changes every downstream number.

## Sanity anchors

- M/D/1 ratios: `1.009 / 0.984 / 1.108`.
- Part 2b spread: `50.7` to `119.7` ms.
- Coordinated omission gap: `9.7x`.

If your numbers are close but not equal, the almost-certain cause is RNG
consumption order — the same generator must produce the same stream of draws
in the same sequence as the reference.
