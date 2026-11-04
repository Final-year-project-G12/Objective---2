"""
src/optimize/nsga2.py
========================
Hand-written NSGA-II (Deb et al. 2002), ported from Manvitha's Rajasthan
report ("G9 S4/S5"): "NSGA-II on the winning surrogate (3 seeds, objectives
-g_window, -g_annual, d_overheat, constraint PCM peak at most 65 C) ...
SBX + polynomial mutation, constrained domination, exact hypervolume, 3
seeds (src/optimize/nsga2.py)" -- the report's own file path for this
module, which is why this file uses the same path on the Tamil Nadu side.

`pymoo` (which would have given a ready-made, battle-tested NSGA-II) is
NOT installed in this environment (checked 2026-10-28) -- this is a
from-scratch implementation of the standard textbook algorithm, not a
simplified stand-in: fast non-dominated sort, crowding distance, SBX
crossover, polynomial mutation, binary tournament selection, constrained
domination (a feasible solution always beats an infeasible one; among two
infeasible solutions, the smaller constraint violation wins). Minimization
convention throughout -- callers negate any objective they want to
maximize (e.g. useful_energy_kWh -> -useful_energy_kWh), exactly as
Rajasthan's own report does ("-g_window, -g_annual").

Validated against a synthetic bi-objective benchmark (ZDT1), not just the
real (slow) PCM simulator -- see tests/test_nsga2.py once the test suite
step adds it; docs_objective2/RAJASTHAN_METHOD_PORT_PROGRESS.md logs the
validation run.
"""

from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass
class NSGA2Result:
    X: np.ndarray                  # (pop_size, n_vars) final population decision vectors
    F: np.ndarray                  # (pop_size, n_obj) final population objective values
    G: np.ndarray                  # (pop_size,) constraint violation (0 = feasible)
    fronts: list                   # list of index arrays, front[0] = non-dominated set
    history_hypervolume: list = field(default_factory=list)   # per-generation HV, for convergence tracking


def _dominates(f_a, g_a, f_b, g_b) -> bool:
    """Constrained domination (Deb's constraint-handling method): a
    solution with LOWER constraint violation always wins; among two
    feasible (g=0) solutions, standard Pareto dominance on the objectives."""
    if g_a > 0 or g_b > 0:
        return g_a < g_b
    return bool(np.all(f_a <= f_b) and np.any(f_a < f_b))


def fast_non_dominated_sort(F: np.ndarray, G: np.ndarray) -> list:
    n = len(F)
    dominated_by = [set() for _ in range(n)]
    domination_count = np.zeros(n, dtype=int)
    fronts = [[]]

    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            if _dominates(F[p], G[p], F[q], G[q]):
                dominated_by[p].add(q)
            elif _dominates(F[q], G[q], F[p], G[p]):
                domination_count[p] += 1
        if domination_count[p] == 0:
            fronts[0].append(p)

    i = 0
    while fronts[i]:
        next_front = []
        for p in fronts[i]:
            for q in dominated_by[p]:
                domination_count[q] -= 1
                if domination_count[q] == 0:
                    next_front.append(q)
        i += 1
        fronts.append(next_front)
    fronts.pop()   # last appended front is always empty
    return [np.array(f, dtype=int) for f in fronts]


def crowding_distance(F_front: np.ndarray) -> np.ndarray:
    n, m = F_front.shape
    if n <= 2:
        return np.full(n, np.inf)
    dist = np.zeros(n)
    for obj in range(m):
        order = np.argsort(F_front[:, obj])
        dist[order[0]] = np.inf
        dist[order[-1]] = np.inf
        f_min, f_max = F_front[order[0], obj], F_front[order[-1], obj]
        denom = f_max - f_min
        if denom <= 0:
            continue
        for k in range(1, n - 1):
            dist[order[k]] += (F_front[order[k + 1], obj] - F_front[order[k - 1], obj]) / denom
    return dist


def sbx_crossover(p1: np.ndarray, p2: np.ndarray, lo: np.ndarray, hi: np.ndarray,
                   eta: float, prob: float, rng: np.random.Generator):
    c1, c2 = p1.copy(), p2.copy()
    if rng.random() > prob:
        return c1, c2
    for i in range(len(p1)):
        if rng.random() > 0.5 or abs(p1[i] - p2[i]) < 1e-14:
            continue
        x1, x2 = min(p1[i], p2[i]), max(p1[i], p2[i])
        u = rng.random()
        beta = 1.0 + 2.0 * (x1 - lo[i]) / max(x2 - x1, 1e-14)
        alpha = 2.0 - beta ** (-(eta + 1))
        beta_q = (u * alpha) ** (1.0 / (eta + 1)) if u <= 1.0 / alpha else (1.0 / (2.0 - u * alpha)) ** (1.0 / (eta + 1))
        child1 = 0.5 * ((x1 + x2) - beta_q * (x2 - x1))

        beta2 = 1.0 + 2.0 * (hi[i] - x2) / max(x2 - x1, 1e-14)
        alpha2 = 2.0 - beta2 ** (-(eta + 1))
        beta_q2 = (u * alpha2) ** (1.0 / (eta + 1)) if u <= 1.0 / alpha2 else (1.0 / (2.0 - u * alpha2)) ** (1.0 / (eta + 1))
        child2 = 0.5 * ((x1 + x2) + beta_q2 * (x2 - x1))

        c1[i] = np.clip(child1, lo[i], hi[i])
        c2[i] = np.clip(child2, lo[i], hi[i])
    return c1, c2


def polynomial_mutation(x: np.ndarray, lo: np.ndarray, hi: np.ndarray, eta: float,
                         prob: float, rng: np.random.Generator) -> np.ndarray:
    y = x.copy()
    for i in range(len(x)):
        if rng.random() > prob:
            continue
        delta1 = (y[i] - lo[i]) / max(hi[i] - lo[i], 1e-14)
        delta2 = (hi[i] - y[i]) / max(hi[i] - lo[i], 1e-14)
        u = rng.random()
        mut_pow = 1.0 / (eta + 1.0)
        if u < 0.5:
            xy = 1.0 - delta1
            val = 2.0 * u + (1.0 - 2.0 * u) * (xy ** (eta + 1.0))
            delta_q = val ** mut_pow - 1.0
        else:
            xy = 1.0 - delta2
            val = 2.0 * (1.0 - u) + 2.0 * (u - 0.5) * (xy ** (eta + 1.0))
            delta_q = 1.0 - val ** mut_pow
        y[i] = np.clip(y[i] + delta_q * (hi[i] - lo[i]), lo[i], hi[i])
    return y


def _tournament_select(pop_rank: np.ndarray, pop_crowd: np.ndarray, rng: np.random.Generator) -> int:
    i, j = rng.integers(0, len(pop_rank), size=2)
    if pop_rank[i] < pop_rank[j]:
        return i
    if pop_rank[j] < pop_rank[i]:
        return j
    return i if pop_crowd[i] > pop_crowd[j] else j


def hypervolume(F: np.ndarray, ref_point: np.ndarray) -> float:
    """Exact hypervolume (minimization convention) for 2 or 3 objectives --
    exact, not Monte Carlo, matching the report's "exact hypervolume". Only
    points that dominate ref_point contribute.

    2-D case: sort points ascending by x; the strip between consecutive
    x-values is covered (in y) by the smallest y seen so far scanning left
    to right (a point only covers x >= its own x, so the relevant
    candidates for strip i are every point at or before it in ascending-x
    order -- a running PREFIX minimum of y, not a "running best, skip if
    not improving" rule, which undercounts: e.g. points (0,1) and (1,0)
    against ref=(2,2) have true hypervolume 3 (the union of [0,2]x[1,2] and
    [1,2]x[0,2]), found and fixed during validation (2026-10-28) after the
    first version returned 2 and produced impossible negative hypervolumes
    during NSGA-II's elitism check."""
    pts = F[np.all(F < ref_point, axis=1)]
    if len(pts) == 0:
        return 0.0
    m = F.shape[1]
    if m == 1:
        return float(ref_point[0] - pts[:, 0].min())
    if m == 2:
        order = np.argsort(pts[:, 0])
        xs, ys = pts[order, 0], pts[order, 1]
        n = len(xs)
        hv = 0.0
        running_min_y = np.inf
        for i in range(n):
            running_min_y = min(running_min_y, ys[i])
            x_next = xs[i + 1] if i + 1 < n else ref_point[0]
            width = x_next - xs[i]
            if width > 0:
                hv += width * (ref_point[1] - running_min_y)
        return float(hv)
    if m == 3:
        # slice along the 3rd objective into 2-D hypervolume strips
        order = pts[np.argsort(pts[:, 2])]
        hv, prev_z = 0.0, ref_point[2]
        active = np.empty((0, 2))
        for row in order[::-1]:
            z = row[2]
            hv_2d = hypervolume(np.vstack([active, row[:2]]) if len(active) else row[:2].reshape(1, 2),
                                 ref_point[:2])
            hv += hv_2d * (prev_z - z)
            prev_z = z
            active = np.vstack([active, row[:2]]) if len(active) else row[:2].reshape(1, 2)
        return float(hv)
    raise NotImplementedError("hypervolume implemented for <=3 objectives only")


def run_nsga2(evaluate_fn: Callable[[np.ndarray], tuple], lo: np.ndarray, hi: np.ndarray,
              pop_size: int = 100, n_gen: int = 100, seed: int = 0,
              sbx_eta: float = 15.0, sbx_prob: float = 0.9,
              mut_eta: float = 20.0, mut_prob: float = None,
              ref_point: np.ndarray = None, track_hypervolume: bool = True) -> NSGA2Result:
    """evaluate_fn(X) -> (F, G): X is (n, n_vars), F is (n, n_obj)
    (minimization), G is (n,) constraint violation (0 = feasible, >0 = how
    infeasible). Evaluated in ONE batched call per generation (parent +
    offspring together) so the caller can parallelize evaluate_fn
    internally (e.g. ProcessPoolExecutor across the real simulator) without
    this function needing to know about it."""
    rng = np.random.default_rng(seed)
    n_vars = len(lo)
    mut_prob = mut_prob if mut_prob is not None else 1.0 / n_vars

    X = lo + rng.random((pop_size, n_vars)) * (hi - lo)
    F, G = evaluate_fn(X)
    history_hv = []

    for gen in range(n_gen):
        fronts = fast_non_dominated_sort(F, G)
        rank = np.empty(len(X), dtype=int)
        crowd = np.empty(len(X))
        for r, front in enumerate(fronts):
            rank[front] = r
            crowd[front] = crowding_distance(F[front])

        # offspring via tournament selection + SBX + polynomial mutation
        offspring = np.empty((pop_size, n_vars))
        for k in range(0, pop_size, 2):
            i1 = _tournament_select(rank, crowd, rng)
            i2 = _tournament_select(rank, crowd, rng)
            c1, c2 = sbx_crossover(X[i1], X[i2], lo, hi, sbx_eta, sbx_prob, rng)
            c1 = polynomial_mutation(c1, lo, hi, mut_eta, mut_prob, rng)
            c2 = polynomial_mutation(c2, lo, hi, mut_eta, mut_prob, rng)
            offspring[k] = c1
            if k + 1 < pop_size:
                offspring[k + 1] = c2

        F_off, G_off = evaluate_fn(offspring)
        X_comb = np.vstack([X, offspring])
        F_comb = np.vstack([F, F_off])
        G_comb = np.concatenate([G, G_off])

        fronts_comb = fast_non_dominated_sort(F_comb, G_comb)
        new_idx = []
        for front in fronts_comb:
            if len(new_idx) + len(front) <= pop_size:
                new_idx.extend(front.tolist())
            else:
                remaining = pop_size - len(new_idx)
                cd = crowding_distance(F_comb[front])
                order = np.argsort(-cd)
                new_idx.extend(front[order[:remaining]].tolist())
                break

        X = X_comb[new_idx]
        F = F_comb[new_idx]
        G = G_comb[new_idx]

        if track_hypervolume:
            rp = ref_point if ref_point is not None else F.max(axis=0) * 1.1 + 1e-6
            front0 = fast_non_dominated_sort(F, G)[0]
            history_hv.append(hypervolume(F[front0], rp))

    fronts_final = fast_non_dominated_sort(F, G)
    return NSGA2Result(X=X, F=F, G=G, fronts=fronts_final, history_hypervolume=history_hv)
