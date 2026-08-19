# Solution walkthrough

## The five-line simulator is the trustworthy part

`simulate_fcfs` is deliberately too simple to be wrong: one server, arrivals
in order, `start = max(arrival, server_free)`. That simplicity is what makes
Part 2 meaningful — when the measured mean lands within 1% of
Pollaczek–Khinchine at moderate load, the agreement validates the
*measurement pipeline* (percentile code, warmup trimming, accounting of what
counts as "wait") rather than the simulator. Calibration only works when one
side of the comparison is beyond suspicion.

## What each part actually established

**Part 1.** Two failure modes of the innocuous percentile: float rank
arithmetic (p99.9 silently becoming the maximum) and sample-size dishonesty
(p99 of n < 100 *is* the maximum). Both produce plausible-looking numbers;
neither produces an error message. The `Fraction` fix costs nothing and
removes an entire bug class.

**Part 2.** The M/D/1 ratios — `1.009`, `0.984`, `1.108` — carry a second
lesson in their ordering: accuracy degrades as $\rho$ rises, with all three
runs using identical sample counts. Waits near saturation are dominated by
rare long busy periods, so the variance of the estimator grows exactly where
the system is most interesting. Part 2b makes that unmissable: twenty
1000-request benchmarks of one fixed server span `50.7` to `119.7` ms
against a 90 ms truth. Any pair of those runs, presented as before/after,
"demonstrates" a 2× regression that does not exist. Run length is a
correctness parameter.

**Part 3.** The mean obeys the closed form at every load (the worst
deviation in the table is ~7%), while p99 must be read off the simulation.
The pairing is the point: theory pins the part of the distribution it can,
measurement covers the rest, and disagreement in the pinned part means the
benchmark — not the theory — is broken. The hockey stick from 3.1 s to
41.7 s of p99 TTFT across a 2× load range is the operational content: near
saturation, tiny load shifts dwarf every optimization this course has
taught, which is why capacity planning and admission control sit upstream of
kernels in the hierarchy of things that determine user experience.

**Part 4.** The `9.7x` gap needs no subtle statistics to detect — it is
enormous — yet the erroneous setup is the *natural* one. A loop that awaits
each response before sending the next is how nearly everyone writes their
first benchmark, and it produces a load generator that backs off in perfect
synchrony with server congestion. The measured `1.22` req/s achieved (versus
`1.36` targeted) is the visible symptom: the closed loop could not even
offer the intended load, and the requests it failed to send are precisely
the ones that would have recorded the worst latencies.

## The RNG discipline

Every random draw flows through explicitly seeded `random.Random` instances,
consumed in a documented order. That is what makes a *statistical* benchmark
gradeable byte-for-byte, and it is worth imitating outside coursework:
seeded load generators make performance regressions bisectable, because two
runs differ only by the code change, not by the traffic.

## What would change on a real engine

The single-server model compresses continuous batching into a service-time
distribution. On a real engine: TTFT gains a network term and a scheduling
term (measure client-side); ITL becomes a distribution shaped by batch
interference and preemption (report gap percentiles, never the average);
throughput and latency must be reported *as a curve*, because the hockey
stick means either number alone is choosable at will. The theory notes carry
the full checklist — clock locking, warm-state definition, per-phase
percentiles — all of which are this module's lessons with mechanical rather
than statistical causes.
