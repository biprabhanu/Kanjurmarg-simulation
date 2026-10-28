"""
Independent Python re-implementation of FobEngine (engine/FobEngine.java), version 2.

Purpose: a cross-check. It re-creates java.util.Random's documented 48-bit linear congruential
generator, so for the same seed it should reproduce the Java engine's counts exactly. Any
disagreement would reveal a logic error in one of the two implementations.
"""
import math

# ---------------------------------------------------------------------------
# java.util.Random (documented algorithm, Java SE API specification)
# ---------------------------------------------------------------------------
class JavaRandom:
    MULT = 0x5DEECE66D
    ADD = 0xB
    MASK = (1 << 48) - 1

    def __init__(self, seed: int):
        self.state = (seed ^ self.MULT) & self.MASK

    def _next(self, bits: int) -> int:
        self.state = (self.state * self.MULT + self.ADD) & self.MASK
        return self.state >> (48 - bits)

    def next_double(self) -> float:
        return ((self._next(26) << 27) + self._next(27)) * (1.0 / (1 << 53))


# ---------------------------------------------------------------------------
# Inputs (must mirror FobEngine.java)
# ---------------------------------------------------------------------------
GATES = ["Naval Colony", "Huma", "Gandhi Nagar", "Northeast", "Southeast"]
ENTER_RATE = [10.00, 27.20, 33.33, 10.00, 10.00]
LEAVE_RATE = [42.00, 50.00, 6.66, 5.00, 5.00]
EXTRA_SHARE = {1: 0.80, 2: 0.20}
PF1, FOB2, FOB3, SKYWALK = 0, 1, 2, 3
DEFAULT_SPLITS = [
    [0.60, 0.25, 0.15, 0.00],
    [0.55, 0.30, 0.15, 0.00],
    [0.60, 0.35, 0.05, 0.00],
    [0.00, 0.95, 0.00, 0.05],
    [0.00, 0.30, 0.70, 0.00],
]
EXTRA_SPLITS = [               # additional (metro-related) demand: Huma, Gandhi Nagar
    [0.50, 0.35, 0.15, 0.00],
    [0.40, 0.40, 0.20, 0.00],
]
NUM_STREAMS = 12
X_WEST_GATE, X_CONCOURSE, X_PF1, X_FOB_MID, X_PF2, X_SKYWALK, X_EAST_GATE = 4, 12, 24, 36, 48, 70, 78
GATE_Y = [16, 46, 78, 8, 80]
Y_FOB2, Y_FOB3, LANDING = 32, 62, 6


def is_east(g):
    return g in (3, 4)


def gate_of(s):
    return s // 2 if s < 10 else (1 if s == 10 else 2)


def is_entering(s):
    return s >= 10 or s % 2 == 0


def rate(s, additional):
    if s == 10:
        return additional * 0.80
    if s == 11:
        return additional * 0.20
    g = gate_of(s)
    return ENTER_RATE[g] if is_entering(s) else LEAVE_RATE[g]


def split_for_stream(s, splits, extra):
    return extra[s - 10] if s >= 10 else splits[gate_of(s)]


def expected_route_flows(splits, additional, extra=EXTRA_SPLITS):
    flow = [0.0] * 4
    for s in range(NUM_STREAMS):
        lam = rate(s, additional)
        p = split_for_stream(s, splits, extra)
        for r in range(4):
            flow[r] += lam * p[r]
    return flow


def waypoints(g, entering, route):
    gy = GATE_Y[g]
    if not is_east(g):
        if route == PF1:
            path = [(X_WEST_GATE, gy), (X_CONCOURSE, gy), (X_PF1, gy)]
        else:
            fy = Y_FOB2 if route == FOB2 else Y_FOB3
            path = [(X_WEST_GATE, gy), (X_CONCOURSE, gy), (X_CONCOURSE, fy), (X_FOB_MID, fy), (X_PF2, fy), (X_PF2, fy + LANDING)]
    else:
        via2 = route == FOB2
        fy = Y_FOB2 if via2 else Y_FOB3
        land = fy + LANDING if via2 else fy - LANDING
        path = [(X_EAST_GATE, gy), (X_SKYWALK, gy), (X_SKYWALK, fy), (X_FOB_MID, fy), (X_PF1, fy), (X_PF1, land)]
    return path if entering else path[::-1]


def crossing_delay(g, entering, route, speed):
    path = waypoints(g, entering, route)
    k = [i for i, p in enumerate(path) if p[0] == X_FOB_MID][0]
    return sum(math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(k)) / speed


def fob_of(route):
    return 2 if route == FOB2 else (3 if route in (FOB3, SKYWALK) else 0)


def draw_route(rng, probs):
    u = rng.next_double()
    cum, last = 0.0, 0
    for r, p in enumerate(probs):
        if p <= 0:
            continue
        cum += p
        last = r
        if u < cum:
            return r
    return last


def draw_normal(rng):
    u1 = rng.next_double()
    u2 = rng.next_double()
    return math.sqrt(-2.0 * math.log(1.0 - u1)) * math.cos(2.0 * math.pi * u2)


def draw_gamma(rng, shape):
    d = shape - 1.0 / 3.0
    c = 1.0 / math.sqrt(9.0 * d)
    while True:
        x = draw_normal(rng)
        v = 1.0 + c * x
        if v <= 0:
            continue
        v = v * v * v
        u = rng.next_double()
        if u < 1.0 - 0.0331 * x ** 4:
            return d * v
        if math.log(u) < 0.5 * x * x + d * (1.0 - v + math.log(v)):
            return d * v


def noisy_splits(base, kappa, rng):
    out = []
    for g in range(len(base)):
        if kappa <= 0:
            out.append(list(base[g]))
            continue
        vals = [draw_gamma(rng, kappa * p) if p > 0 else 0.0 for p in base[g]]
        tot = sum(vals)
        out.append([v / tot for v in vals])
    return out


def run_replication(seed, additional, base=DEFAULT_SPLITS, kappa=99.0, duration_min=60, speed=1.30, extra=EXTRA_SPLITS):
    horizon = duration_min * 60.0
    noise = JavaRandom(seed * 1000 + 500)
    splits = noisy_splits(base, kappa, noise)
    xsplits = noisy_splits(extra, kappa, noise)
    routes_x = [[0] * 4 for _ in range(2)]
    gen = [0] * NUM_STREAMS
    routes = [[0] * 4 for _ in range(5)]
    fob2 = [0] * duration_min
    fob3 = [0] * duration_min
    for s in range(NUM_STREAMS):
        lam = rate(s, additional)
        if lam <= 0:
            continue
        rng = JavaRandom(seed * 1000 + s)
        g, ent = gate_of(s), is_entering(s)
        t = -math.log(1.0 - rng.next_double()) * 60.0 / lam
        while t < horizon:
            r = draw_route(rng, split_for_stream(s, splits, xsplits))
            gen[s] += 1
            if s >= 10:
                routes_x[s - 10][r] += 1
            else:
                routes[g][r] += 1
            f = fob_of(r)
            if f:
                ct = t + crossing_delay(g, ent, r, speed)
                if ct < horizon:
                    (fob2 if f == 2 else fob3)[int(math.floor(ct / 60.0))] += 1
            t += -math.log(1.0 - rng.next_double()) * 60.0 / lam
    return {"generated": gen, "routes": routes, "routes_extra": routes_x, "splits": splits, "extra_splits": xsplits,
            "fob2": fob2, "fob3": fob3}
