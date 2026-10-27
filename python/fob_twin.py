"""
Independent Python re-implementation of FobEngine (engine/FobEngine.java).

Purpose: a cross-check. It re-creates java.util.Random's documented 48-bit linear
congruential generator so that, for the same seed, it should reproduce the Java engine's
passenger counts exactly. Any disagreement would reveal a logic error in one of the two.
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
# Inputs and geometry (must mirror FobEngine.java)
# ---------------------------------------------------------------------------
ENTRANCES = ["Naval Colony", "Huma", "Gandhi Nagar"]
ENTER_RATE = [10.00, 27.20, 33.33]
LEAVE_RATE = [42.00, 50.00, 6.66]
ENTRANCE_Y = [16, 46, 78]
X_ENTRANCE, X_CONCOURSE, X_PF1, X_FOB_MID, X_PF2 = 4, 12, 24, 36, 48
Y_FOB = {1: 32, 2: 62}
LANDING = 6
PF1, FOB2, FOB3 = 0, 1, 2


def calibrated_probabilities():
    return [65.89 / 169.19, 70.00 / 169.19, 33.30 / 169.19]


def stream_rate(s):
    e = s // 2
    return ENTER_RATE[e] if s % 2 == 0 else LEAVE_RATE[e]


def waypoints(entrance, entering, route):
    ye = ENTRANCE_Y[entrance]
    if route == PF1:
        path = [(X_ENTRANCE, ye), (X_CONCOURSE, ye), (X_PF1, ye)]
    else:
        yf = Y_FOB[route]
        path = [(X_ENTRANCE, ye), (X_CONCOURSE, ye), (X_CONCOURSE, yf),
                (X_FOB_MID, yf), (X_PF2, yf), (X_PF2, yf + LANDING)]
    return path if entering else path[::-1]


def crossing_delay(entrance, entering, route, speed):
    k = 3 if entering else 2
    path = waypoints(entrance, entering, route)
    dist = sum(math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(k))
    return dist / speed


def draw_route(rng, probs):
    u = rng.next_double()
    cum = 0.0
    for r, p in enumerate(probs):
        cum += p
        if u < cum:
            return r
    return len(probs) - 1


def run_replication(seed, multiplier, probs, duration_min=60, speed=1.30):
    horizon = duration_min * 60.0
    gen = [0] * 6
    routes = [0, 0, 0]
    fob2 = [0] * duration_min
    fob3 = [0] * duration_min
    for s in range(6):
        rng = JavaRandom(seed * 1000 + s)
        lam = stream_rate(s) * multiplier
        entrance, entering = s // 2, s % 2 == 0
        t = -math.log(1.0 - rng.next_double()) * 60.0 / lam
        while t < horizon:
            r = draw_route(rng, probs)
            gen[s] += 1
            routes[r] += 1
            if r != PF1:
                ct = t + crossing_delay(entrance, entering, r, speed)
                if ct < horizon:
                    (fob2 if r == FOB2 else fob3)[int(math.floor(ct / 60.0))] += 1
            t += -math.log(1.0 - rng.next_double()) * 60.0 / lam
    return {"generated": gen, "routes": routes, "fob2": fob2, "fob3": fob3}
