# Theory notes: queues, tails, and honest clocks

## 1. Pollaczek–Khinchine, where it comes from

The M/G/1 result the module uses is worth deriving once. A request arriving
at a random time must wait for (a) the residual service of whoever is on the
server now, and (b) the full service of everyone in the queue ahead of it.
Write $W$ for the mean wait, $\lambda$ for the arrival rate, $S$ for service.

By PASTA (Poisson arrivals see time averages), the arriver finds the server
busy with probability $\rho = \lambda \mathbb{E}[S]$, and the mean *residual*
service it sees is $\mathbb{E}[S^2]/(2\mathbb{E}[S])$ — the length-biased
residual, larger than $\mathbb{E}[S]/2$ whenever service varies, because a
random observer is more likely to land inside a long service than a short
one. By Little's law (module 1's other queueing tool), the mean queue length
is $\lambda W$, each contributing $\mathbb{E}[S]$:

$$
W = \underbrace{\rho \cdot \frac{\mathbb{E}[S^2]}{2\mathbb{E}[S]}}_{\text{residual}}
+ \underbrace{\lambda W \,\mathbb{E}[S]}_{\text{queue ahead}}
\;\;\Longrightarrow\;\;
W = \frac{\lambda \mathbb{E}[S^2]}{2(1-\rho)}
$$

Read the two factors separately, because they are the two levers a serving
system has. The $1/(1-\rho)$ factor is load: nothing but admission control
touches it. The $\mathbb{E}[S^2]$ factor is *service variability*: for fixed
mean work, cutting variance cuts everyone's wait. That is the queueing-theory
justification for chunked prefill (module 11): splitting a 20k-token prefill
into chunks does not reduce its work, but it slashes the second moment of
the per-step service distribution that decode requests experience — the
formula says exactly why interleaving helps the p99 of bystanders.

The length-biased residual term is also the honest answer to a common
confusion: "why is my TTFT bad when utilization is only 70%?" Because what an
arriving request samples is not the average service but the second-moment-
weighted one, and heavy-tailed request lengths make that weighting brutal.

## 2. Why the tail is not the mean, quantitatively

For M/D/1 the full waiting-time distribution has an exponential tail:
$\Pr[W > t] \sim C e^{-\theta t}$ where $\theta \to 0$ as $\rho \to 1$. Two
consequences the module's tables display:

- p99 is roughly $W \cdot \ln(100) / $ (a distribution-dependent constant) —
  proportional to the mean but with a multiplier that grows with service
  variability. In the Part 3 sweep, p99/mean sits around 4–7×.
- The tail exponent degrades like $1-\rho$, so a modest load increase
  stretches the tail *more* than it raises the mean. Between $\rho = 0.9$
  and $0.95$ the measured mean grows 2.2× and the p99 grows 2.4×.

The estimator side is worse. The variance of a sample quantile at level $q$
scales like $q(1-q)/(n f(x_q)^2)$ — and $f(x_q)$, the density at the tail
quantile, is tiny. Combine with the autocorrelation of queue waits (adjacent
requests share busy periods, so effective sample size is far below $n$) and
you get Part 2b's result: 1000-request benchmarks scattered over a 2.4×
range. Rule of thumb: to trust a percentile at level $q$, you want at least
$\sim 30/(1-q)$ *independent* busy periods, not samples — for p99 near
saturation, that is tens of thousands of requests.

## 3. Coordinated omission, precisely

The term is Gil Tene's, from the HdrHistogram work. The general statement: a
measurement process that schedules its own future measurements based on the
system's responses will under-sample the system's bad states. The closed
loop is the canonical case, but the same bug appears as:

- a benchmark that sends the next request when the previous one *finishes*
  (every `for` loop over `await client.send(...)`);
- a latency recorder that timestamps at dequeue instead of at intended send
  time, so queue-buildup time silently vanishes;
- a monitoring agent that polls less often when the host is loaded — the
  metric gaps line up exactly with the incidents.

The repair in each case is the same: fix the *intended* schedule in advance
(open-loop arrivals), and if a request could not even be sent on time, charge
it the delay. When a tool must run closed-loop, the correction is to record
each response's latency as (actual completion − intended send time) under
the fixed schedule — which is what HdrHistogram's correction mode does, and
what Part 4's gap approximates.

One honesty note in the other direction: some production systems really are
closed-loop — an agentic workload that cannot issue its next call until the
previous returns is genuinely self-throttling. The sin is not closed-loop
load; it is closed-loop load *presented as* the open-loop experience of
independent users.

## 4. From the simulator to a GPU: the checklist

The simulation abstracts the server to a service-time distribution. Measuring
the real thing adds mechanical requirements, all of which are module 2's
lessons scaled up:

- **Timestamp at the right layer.** TTFT is client-observed: from request
  send to first streamed token, including network and queueing. An engine's
  self-reported "prefill time" is a different, smaller number.
- **Steady state, not warm start.** Discard the ramp: the first requests hit
  an empty batch queue (flattering) and cold caches — CUDA graphs
  uncaptured, `torch.compile` still compiling, prefix cache empty — which can
  bias either direction. Trim until a windowed mean stabilizes; Part 2b is
  what happens when you do not.
- **Lock the clocks.** GPU boost clocks drift with temperature; a 10-minute
  benchmark can start 15% faster than it ends. `nvidia-smi -lgc` pins them;
  otherwise interleave the configurations you are comparing.
- **Percentiles per phase.** Aggregate "request latency" mixes TTFT and
  generation length; report TTFT and ITL distributions separately, and ITL
  as the distribution of *gaps*, not total/(tokens−1), which hides stalls —
  a decode preempted for 300 ms shows up in the gap p99 and vanishes in the
  average.
- **Report the load point.** A latency without its utilization is
  meaningless — the hockey stick means the same system yields any latency
  you like at some load. The honest artifact is the whole curve: sweep
  offered load, plot p50/p99 against achieved throughput.

## 5. What the single-server model leaves out

Continuous batching (module 12) makes service times *interact*: admitting a
request slows every other request's ITL slightly, rather than queueing behind
them entirely. The single-server model overstates queueing and understates
interference; the hockey stick, the second-moment sensitivity, and both
statistical pathologies survive unchanged. A finer model — processor sharing
with a batch cap — reproduces ITL interference too, at the cost of the
closed form; once you need that fidelity, you have left calibration territory
and should be measuring the real engine with the discipline above.
