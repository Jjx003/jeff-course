# Measure TTFT and p99 without fooling yourself

Every module in this course has ended with an instruction to measure. Module 2
taught the micro-benchmark half of that skill: warm up, repeat, synchronize,
state your byte-accounting convention. This module teaches the other half —
measuring a *serving system* — where the failure modes are statistical rather
than mechanical, and where the standard mistakes do not produce noisy numbers
but confidently wrong ones.

The three numbers that define interactive serving:

- **TTFT** (time to first token): queueing delay plus prefill. What a user
  feels as "did it start responding."
- **ITL** (inter-token latency): the gap between streamed tokens. What a user
  feels as "is it typing fast."
- **p99** of either: the experience of your unluckiest one percent — which,
  for a chat product with millions of requests, is tens of thousands of
  people per day, every day.

You will build the measurement machinery from scratch against a simulated
server, because a simulation is the one setting where the *truth* is
available in closed form — so you can check the measurement itself, which is
the entire point. The queueing model is crude on purpose: a single-server
FCFS queue is to a continuous-batching engine what module 2's roofline was to
a real GPU. It drops enough detail to have a closed form, keeps the two
behaviors that dominate real benchmarks — queueing delay and its explosion
near saturation — and its predictions are floors and shapes, not forecasts.

## Part 1 — The percentile itself

Implement `nearest_rank_percentile`: the smallest sample value with at least
$q$ percent of the data at or below it — sort, take element
$\lceil qn/100 \rceil$ (1-indexed). No interpolation: a p99 that averages two
observed values reports a latency that never happened.

Two traps live inside this three-line function, and the starter makes you hit
both. First, floating point: `0.999 * 1000` is `999.0000000000001`, and
taking `ceil` of it turns p99.9 into the sample maximum — compute the rank in
exact rational arithmetic (`Fraction`). Second, sample size: for $n < 100$,
$\lceil 0.99n \rceil = n$, so **the p99 of fewer than 100 samples is just the
maximum**, and the program computes the exact threshold. The practical rule
scales: to say anything about p99.9 you need thousands of requests, and a
benchmark that reports p99 from a 50-request run is reporting an anecdote
with a decimal point.

## Part 2 — Verify the measurement against a closed form

Implement `simulate_fcfs` — the entire discrete-event simulator is five
lines, because with one server and FCFS order, `start = max(arrival,
server_free)` is the whole scheduling policy.

Then check it against theory. For Poisson arrivals at utilization $\rho$ and
*deterministic* service time $S$, the Pollaczek–Khinchine formula gives the
exact long-run mean queueing delay:

$$
W_{M/D/1} = \frac{\rho S}{2(1-\rho)}
$$

Your simulation reproduces it: measured-to-predicted ratios of `1.009`,
`0.984`, and `1.108` at $\rho = 0.5, 0.7, 0.9$ over 75,000 steady-state
requests. This is the module's version of the course's signature move — the
optimization modules proved their transforms exact; a benchmark harness
cannot be proved exact, but it can be **calibrated against a system whose
true answer is known**, and a harness that has never passed such a test
should not be trusted on a system whose true answer is not.

Note the ratio at $\rho = 0.9$ is the worst of the three even with 75,000
samples. That is not sloppiness; waits near saturation are dominated by rare
long busy periods, so the estimator's variance explodes exactly where the
system gets interesting. Part 2b measures that directly: twenty separate
1000-request benchmarks of the *same server at the same load* report mean
waits from `50.7` to `119.7` ms — a `2.4x` spread around a true value of
90 ms. Any two of those runs "prove" a regression or an optimization. This is
why benchmark length is a correctness parameter, not a politeness.

## Part 3 — The load-latency curve

Make the server LLM-shaped: service = 40 ms of prefill plus 5 ms per token,
token counts uniform in 16..256, and TTFT = wait + prefill. Implement the
general P–K formula

$$
W_{M/G/1} = \frac{\lambda\,\mathbb{E}[S^2]}{2(1-\rho)}
$$

and sweep $\rho$ from 0.5 to 0.95.

![TTFT percentiles and mean against utilization for the simulated server, with the Pollaczek-Khinchine mean overlaid, and a bar chart showing open-loop versus closed-loop percentiles at 98 percent utilization](/courses/model-optimization-systems/bench-latency-vs-load.svg)

Two lessons sit in the resulting table.
The mean tracks the closed form at every load — and the closed form says the
mean is driven by the *second moment* of service time, which is why one 20k
token request in the mix damages everyone's TTFT far more than its own
duration suggests. And the tail is worse than the mean: p99 TTFT goes from
3.1 s at half load to 41.7 s at $\rho = 0.95$, growing faster than the
$1/(1-\rho)$ mean because the tail compounds queueing with unlucky service
draws. The operational consequence is the shape itself: latency versus load
is a hockey stick, "capacity" is not a point but a cliff, and the standard
practice of running fleets at 60–80 percent utilization is this curve read
backwards.

## Part 4 — Coordinated omission

Finally, the lie most benchmark tools tell by default. Implement
`simulate_closed_loop`: $C$ clients that each send a request, **wait for it
to complete**, think, and send the next. Compare it against open-loop
arrivals targeting the same offered load, near saturation ($\rho = 0.98$).

Same server. Same intended load. The open-loop measurement reports a p99
TTFT of `50.8` seconds; the closed-loop measurement reports `5.2` — an
understatement of `9.7x`. The mechanism is in the loop structure: a
closed-loop client that is stuck waiting on a slow request *sends nothing*,
so the generator sheds load precisely when the server is struggling, and the
requests that would have observed the congestion are never sent. Real users
are not so polite — new users arrive regardless of how the current ones are
being treated. Open-loop is the model of that; closed-loop measures a
different, gentler world and is the default behavior of any benchmark script
that loops `send; await; send`.

Do not change the starter constants or the output labels. The grader checks
printed stdout.

## Recap

You built a percentile function that is exact about ranks and honest about
sample sizes, calibrated a queue simulator against the Pollaczek–Khinchine
closed form, mapped the load-latency hockey stick for an LLM-shaped
workload, and measured a 9.7× coordinated-omission gap between two load
generators aimed at the same server. The theory notes connect these to real
GPU practice — clock locking, `cuda.synchronize`, and what "warmup" must
mean for a serving benchmark. The next module leaves LLM serving for protein
model workloads, where the numbers being protected are biological rather
than conversational — and where this module's discipline about what a
benchmark actually measured matters just as much.
