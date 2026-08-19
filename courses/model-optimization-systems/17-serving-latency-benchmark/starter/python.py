"""
Latency measurement done honestly: nearest-rank percentiles, an M/D/1 queue
checked against the Pollaczek-Khinchine closed form, the load-latency curve
for an LLM-shaped M/G/1 server, and a demonstration of coordinated omission.

Everything is a seeded simulation, so your output matches the grader
byte for byte. See problem.md for the required output format.
"""

import heapq
import math
import random
from fractions import Fraction

# Part 2: M/D/1 -----------------------------------------------------------
SERVICE_MS = 20.0
N_ARRIVALS = 80_000
WARMUP = 5_000
RHOS_MD1 = [0.5, 0.7, 0.9]

# Part 3/4: LLM-shaped M/G/1 ----------------------------------------------
PREFILL_MS = 40.0
ITL_MS = 5.0
MIN_TOKENS = 16
MAX_TOKENS = 256
RHOS_SWEEP = [0.5, 0.7, 0.8, 0.9, 0.95]
N_SWEEP = 100_000
WARMUP_SWEEP = 10_000

# Part 4: coordinated omission --------------------------------------------
N_CO = 20_000
CO_RHO = 0.98
N_CLIENTS = 16


def nearest_rank_percentile(sorted_values: list[float], q: float) -> float:
    """Nearest-rank percentile: the smallest value with at least q% of the
    sample at or below it. `sorted_values` must already be sorted.

    rank = ceil(q/100 * n), 1-indexed; return sorted_values[rank - 1].

    The rank is computed in exact rational arithmetic: in floats,
    0.999 * 1000 = 999.0000000000001, and ceil of that is 1000 - an
    off-by-one that silently turns p99.9 into the sample maximum.

    TODO 1: compute the rank with math.ceil(Fraction(str(q)) / 100 * n),
    clamp it to [1, n], and return the 1-indexed element.
    """
    raise NotImplementedError


def simulate_fcfs(interarrivals: list[float], services: list[float]) -> list[float]:
    """Single-server FCFS queue. Returns each request's wait (queue delay,
    excluding its own service).

    TODO 2: walk the arrivals in order, tracking the current time and when
    the server frees up. A request starts at max(arrival, server_free); its
    wait is start - arrival; serving it pushes server_free to start + service.
    """
    raise NotImplementedError


def pk_wait_deterministic(rho: float, service: float) -> float:
    """Pollaczek-Khinchine mean wait for M/D/1: W = rho * S / (2 (1 - rho)).

    TODO 3: one line. This is the deterministic-service special case of the
    general formula below (E[S^2] = S^2 for a constant).
    """
    raise NotImplementedError


def pk_wait_general(lam: float, rho: float, es2: float) -> float:
    """Pollaczek-Khinchine mean wait for M/G/1: W = lam * E[S^2] / (2 (1 - rho)).

    TODO 4: one line. The second moment is what makes variable service
    hurt: two service distributions with the same mean give different waits.
    """
    raise NotImplementedError


def sample_service(rng: random.Random) -> float:
    """One LLM-shaped request: fixed prefill plus a uniform token count."""
    n_tokens = rng.randint(MIN_TOKENS, MAX_TOKENS)
    return PREFILL_MS + ITL_MS * n_tokens


def simulate_closed_loop(
    n_clients: int, think_mean: float, n_requests: int, rng: random.Random
) -> tuple[list[float], float]:
    """Closed-loop load: each client sends, waits for completion, thinks,
    repeats. Returns (waits, total_time). FCFS service in arrival order.

    TODO 5: seed a heap with each client's first send time,
    rng.expovariate(1.0 / think_mean). Then n_requests times: pop the
    earliest pending arrival, start it at max(arrival, server_free), draw a
    service with sample_service(rng), record the wait, advance server_free,
    and push the client's next send at finish + a fresh think time. Return
    the waits and the final finish time.

    The heap keeps FCFS order among pending sends, and no client ever has
    two requests outstanding - which is exactly the property that causes
    coordinated omission.
    """
    raise NotImplementedError


def main() -> None:
    print("=== Measuring latency without fooling yourself ===")
    print()

    # --- Part 1 -----------------------------------------------------------
    print("--- Part 1: the percentile itself ---")
    ladder = list(range(1, 1001))
    p50 = nearest_rank_percentile(ladder, 50)
    p90 = nearest_rank_percentile(ladder, 90)
    p99 = nearest_rank_percentile(ladder, 99)
    p999 = nearest_rank_percentile(ladder, 99.9)
    print(f"nearest-rank percentiles of 1..1000: p50={p50} p90={p90} p99={p99} p99.9={p999}")
    small = list(range(1, 21))
    p99_small = nearest_rank_percentile(small, 99)
    print(f"p99 of a 20-sample run: {p99_small} (that is just the sample maximum)")
    n_honest = next(n for n in range(2, 10_000)
                    if math.ceil(0.99 * n) < n)
    print(f"smallest n where p99 is not the maximum: {n_honest}")
    print()

    # --- Part 2 -----------------------------------------------------------
    print("--- Part 2: M/D/1 against Pollaczek-Khinchine ---")
    print(f"deterministic service {SERVICE_MS} ms, {N_ARRIVALS} arrivals per load, first {WARMUP} dropped")
    md1_ratios = []
    for rho in RHOS_MD1:
        rng = random.Random(1000 + int(rho * 100))
        lam = rho / SERVICE_MS
        gaps = [rng.expovariate(lam) for _ in range(N_ARRIVALS)]
        waits = simulate_fcfs(gaps, [SERVICE_MS] * N_ARRIVALS)
        steady = waits[WARMUP:]
        measured = sum(steady) / len(steady)
        predicted = pk_wait_deterministic(rho, SERVICE_MS)
        ratio = measured / predicted
        md1_ratios.append(ratio)
        print(f"rho={rho:.2f}  measured mean wait {measured:7.3f} ms   P-K {predicted:7.3f} ms   ratio {ratio:.3f}")
    print()

    print("--- Part 2b: twenty short benchmarks of the same server ---")
    short_means = []
    for run in range(20):
        rng = random.Random(3000 + run)
        lam = 0.9 / SERVICE_MS
        gaps = [rng.expovariate(lam) for _ in range(1000)]
        waits = simulate_fcfs(gaps, [SERVICE_MS] * 1000)
        short_means.append(sum(waits) / len(waits))
    short_sorted = sorted(short_means)
    spread = short_sorted[-1] / short_sorted[0]
    print(f"rho=0.90, 1000 requests per run, 20 seeds: mean wait ranges "
          f"{short_sorted[0]:.1f} to {short_sorted[-1]:.1f} ms ({spread:.1f}x spread)")
    print(f"long-run truth (P-K): {pk_wait_deterministic(0.9, SERVICE_MS):.1f} ms")
    print("(near saturation, a short benchmark measures which busy periods you")
    print(" happened to catch, not the server)")
    print()

    # --- Part 3 -----------------------------------------------------------
    print("--- Part 3: the load-latency curve (prefill + tokens x ITL) ---")
    mean_tokens = (MIN_TOKENS + MAX_TOKENS) / 2.0
    mean_service = PREFILL_MS + ITL_MS * mean_tokens
    print(f"service = {PREFILL_MS} ms prefill + tokens x {ITL_MS} ms, tokens uniform {MIN_TOKENS}..{MAX_TOKENS}"
          f" -> mean {mean_service:.1f} ms")
    print(f"{'rho':>5} {'req/s':>7} {'wait meas':>10} {'wait P-K':>9} {'ttft p50':>9} {'ttft p99':>9}")
    sweep_p99 = []
    for rho in RHOS_SWEEP:
        rng = random.Random(2000 + int(rho * 100))
        lam = rho / mean_service  # requests per ms
        gaps = [rng.expovariate(lam) for _ in range(N_SWEEP)]
        services = [sample_service(rng) for _ in range(N_SWEEP)]
        waits = simulate_fcfs(gaps, services)
        steady = waits[WARMUP_SWEEP:]
        es2 = sum(s * s for s in services) / len(services)
        measured = sum(steady) / len(steady)
        predicted = pk_wait_general(lam, rho, es2)
        ttft = sorted(w + PREFILL_MS for w in steady)
        t50 = nearest_rank_percentile(ttft, 50)
        t99 = nearest_rank_percentile(ttft, 99)
        sweep_p99.append(t99)
        print(f"{rho:>5.2f} {lam * 1000:>7.2f} {measured:>10.1f} {predicted:>9.1f} {t50:>9.1f} {t99:>9.1f}")
    print("(the mean has a closed form; the tail does not - you have to measure it)")
    print()

    # --- Part 4 -----------------------------------------------------------
    print("--- Part 4: coordinated omission ---")
    lam = CO_RHO / mean_service
    rng_open = random.Random(7)
    gaps = [rng_open.expovariate(lam) for _ in range(N_CO)]
    services = [sample_service(rng_open) for _ in range(N_CO)]
    open_waits = simulate_fcfs(gaps, services)
    open_ttft = sorted(w + PREFILL_MS for w in open_waits[WARMUP_SWEEP:])
    open_p50 = nearest_rank_percentile(open_ttft, 50)
    open_p99 = nearest_rank_percentile(open_ttft, 99)

    think_mean = N_CLIENTS / lam - mean_service
    rng_closed = random.Random(8)
    closed_waits, total_time = simulate_closed_loop(N_CLIENTS, think_mean, N_CO, rng_closed)
    closed_ttft = sorted(w + PREFILL_MS for w in closed_waits[WARMUP_SWEEP:])
    closed_p50 = nearest_rank_percentile(closed_ttft, 50)
    closed_p99 = nearest_rank_percentile(closed_ttft, 99)
    closed_rate = N_CO / total_time * 1000

    print(f"target load: rho={CO_RHO} -> {lam * 1000:.2f} req/s on a {1000 / mean_service:.2f} req/s server")
    print(f"open loop   (arrivals keep coming): ttft p50 {open_p50:9.1f} ms   p99 {open_p99:9.1f} ms")
    print(f"closed loop ({N_CLIENTS} clients, think {think_mean / 1000:.2f} s): "
          f"ttft p50 {closed_p50:9.1f} ms   p99 {closed_p99:9.1f} ms   ({closed_rate:.2f} req/s achieved)")
    understate = open_p99 / closed_p99
    print(f"closed-loop p99 understates open-loop p99 by {understate:.1f}x")
    print("(each waiting client stops sending, so the load generator backs off")
    print(" exactly when the server struggles - the missing requests are the slow ones)")
    print()

    assert (p50, p90, p99, p999) == (500, 900, 990, 999)
    assert p99_small == 20 and n_honest == 100
    assert all(0.85 < r < 1.15 for r in md1_ratios)
    assert spread > 2.0
    assert all(b > a for a, b in zip(sweep_p99, sweep_p99[1:]))
    assert understate > 2.0
    print("=== all checks passed ===")


if __name__ == "__main__":
    main()
