"""
scripts/tn_validate_fast_solve.py
====================================
Proves the banded `_solve_step` solves the SAME system as her original dense
`_solve_step_dense`, and measures what the change bought.

`_solve_step` is compiled into `_kernel` by numba, so it cannot be swapped at
runtime -- validation has to attack the function directly. Two parts:

  1. RANDOMISED EQUIVALENCE. Thousands of random but physically-shaped systems
     across every k_ret (including the in-band k_ret = 0 and 1 branches) and
     both circ states, comparing the two solvers elementwise. This is the real
     proof: same matrix, same right-hand side, same answer.

  2. RESIDUAL CHECK. ||A x - r|| / ||r|| using her own dense assembly, so a
     bug that happened to agree between the two paths would still show up.

Run:  python scripts/tn_validate_fast_solve.py [n_trials]
"""

import sys
import time
from pathlib import Path

import numpy as np
from numba import njit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.simulation.tank_model_multinode import _solve_step, _solve_step_dense  # noqa: E402


# Timed from INSIDE njit. Calling either solver from Python costs ~20 us of
# dispatch overhead, which is larger than the solve itself and hides the
# difference entirely -- `_kernel` calls it compiled-to-compiled, so that is
# how it has to be measured.
def _make_loop(solver):
    @njit(cache=False)
    def loop(T, Tp, UA, m_w, loss_ua, tamb, N, cp, mains, mdot_d, mdot_c, circ,
             k_ret, a, b, kcond, dts, reps):
        acc = 0.0
        for _ in range(reps):
            x = solver(T, Tp, UA, m_w, loss_ua, tamb, N, cp, mains, mdot_d,
                       mdot_c, circ, k_ret, a, b, kcond, dts)
            acc += x[0]          # consume the result so nothing is optimised away
        return acc
    return loop


_loop_fast = _make_loop(_solve_step)
_loop_dense = _make_loop(_solve_step_dense)


def _random_case(rng, N):
    """A system shaped like the ones the kernel actually produces."""
    return dict(
        T=rng.uniform(20.0, 75.0, N),
        Tp=rng.uniform(20.0, 70.0, N),
        UA=rng.uniform(0.0, 400.0, N) * (rng.random(N) > 0.3),
        m_w=rng.uniform(5.0, 15.0, N),
        loss_ua=rng.uniform(0.1, 3.0, N),
        tamb=float(rng.uniform(15.0, 40.0)),
        N=N,
        cp=4186.0,
        mains=float(rng.uniform(20.0, 32.0)),
        mdot_d=float(rng.choice([0.0, rng.uniform(0.0, 0.05)])),
        mdot_c=float(rng.uniform(0.005, 0.06)),
        circ=bool(rng.random() > 0.25),
        k_ret=int(rng.integers(0, N)),
        a=float(rng.uniform(0.0, 4000.0)),
        b=float(rng.uniform(0.0, 60.0)),
        kcond=float(rng.uniform(0.0, 5.0)),
        dts=float(rng.choice([37.5, 75.0, 150.0, 300.0])),
    )


def _assemble_dense(c):
    """Her assembly, rebuilt here so the residual is checked against the
    matrix she defines rather than against either solver."""
    N, cp = c["N"], c["cp"]
    A = np.zeros((N, N))
    r = np.zeros(N)
    ext_in = np.zeros(N)
    ext_out = np.zeros(N)
    ext_in[0] += c["mdot_d"]
    ext_out[N - 1] += c["mdot_d"]
    if c["circ"]:
        ext_out[0] += c["mdot_c"]
        ext_in[c["k_ret"]] += c["mdot_c"]
    F = np.zeros(max(N - 1, 1))
    run = 0.0
    for i in range(N - 1):
        run += ext_in[i] - ext_out[i]
        F[i] = run
    for i in range(N):
        A[i, i] += c["m_w"][i] * cp / c["dts"] + c["loss_ua"][i] + c["UA"][i] + ext_out[i] * cp
        r[i] += (c["m_w"][i] * cp / c["dts"] * c["T"][i] + c["loss_ua"][i] * c["tamb"]
                 + c["UA"][i] * c["Tp"][i])
        if i == 0:
            r[0] += c["mdot_d"] * cp * c["mains"]
        if i > 0:
            Fb = F[i - 1]
            if Fb > 0:
                A[i, i - 1] -= Fb * cp
            else:
                A[i, i] -= Fb * cp
            A[i, i] += c["kcond"]
            A[i, i - 1] -= c["kcond"]
        if i < N - 1:
            Fa = F[i]
            if Fa > 0:
                A[i, i] += Fa * cp
            else:
                A[i, i + 1] += Fa * cp
            A[i, i] += c["kcond"]
            A[i, i + 1] -= c["kcond"]
    if c["circ"]:
        A[c["k_ret"], 0] -= (c["mdot_c"] * cp - c["b"])
        r[c["k_ret"]] += c["a"]
    return A, r


def _call(fn, c):
    return fn(c["T"], c["Tp"], c["UA"], c["m_w"], c["loss_ua"], c["tamb"], c["N"],
              c["cp"], c["mains"], c["mdot_d"], c["mdot_c"], c["circ"], c["k_ret"],
              c["a"], c["b"], c["kcond"], c["dts"])


def main():
    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    rng = np.random.default_rng(20261029)

    # warm both JITs before anything is timed or compared
    warm = _random_case(rng, 10)
    _call(_solve_step, warm)
    _call(_solve_step_dense, warm)

    worst_diff = 0.0
    worst_res_fast = 0.0
    worst_res_dense = 0.0
    worst_case = None
    by_kret = {}

    for _ in range(n_trials):
        N = int(rng.integers(2, 13))
        c = _random_case(rng, N)
        xf = _call(_solve_step, c)
        xd = _call(_solve_step_dense, c)

        scale = max(np.abs(xd).max(), 1.0)
        d = float(np.abs(xf - xd).max() / scale)
        if d > worst_diff:
            worst_diff, worst_case = d, (N, c["k_ret"], c["circ"])

        A, r = _assemble_dense(c)
        nr = max(np.linalg.norm(r), 1.0)
        worst_res_fast = max(worst_res_fast, float(np.linalg.norm(A @ xf - r) / nr))
        worst_res_dense = max(worst_res_dense, float(np.linalg.norm(A @ xd - r) / nr))

        k = "in-band (k_ret<=1)" if c["k_ret"] <= 1 or not c["circ"] else "out-of-band"
        by_kret[k] = max(by_kret.get(k, 0.0), d)

    print(f"{n_trials} random systems, N in [2,12], all k_ret, circ on/off")
    print(f"  worst relative elementwise difference : {worst_diff:.3e}   "
          f"(worst at N={worst_case[0]}, k_ret={worst_case[1]}, circ={worst_case[2]})")
    for k in sorted(by_kret):
        print(f"    {k:22s}: {by_kret[k]:.3e}")
    print(f"  worst residual ||Ax-r||/||r||  banded : {worst_res_fast:.3e}")
    print(f"  worst residual ||Ax-r||/||r||  dense  : {worst_res_dense:.3e}")

    # timing at the production shape, measured inside njit
    c = _random_case(rng, 10)
    c["circ"], c["k_ret"] = True, 6

    def timed(loop, reps):
        args = (c["T"], c["Tp"], c["UA"], c["m_w"], c["loss_ua"], c["tamb"], c["N"],
                c["cp"], c["mains"], c["mdot_d"], c["mdot_c"], c["circ"], c["k_ret"],
                c["a"], c["b"], c["kcond"], c["dts"])
        loop(*args, 10)                      # compile
        t0 = time.perf_counter()
        loop(*args, reps)
        return time.perf_counter() - t0

    reps = 2_000_000
    t_fast = timed(_loop_fast, reps)
    t_dense = timed(_loop_dense, reps)
    # a simulated year is ~24 substeps/h x 8760 h, before melt-band refinement
    per_year = 24 * 8760
    print(f"\n{reps:,} solves at N=10, k_ret=6, timed inside njit:")
    print(f"  banded : {t_fast:7.3f} s  ({1e6*t_fast/reps:6.3f} us/solve)")
    print(f"  dense  : {t_dense:7.3f} s  ({1e6*t_dense/reps:6.3f} us/solve)")
    print(f"  speedup: {t_dense/t_fast:.2f}x on the solve")
    print(f"\n  solver cost per simulated year ({per_year:,} substeps, no melt-band refinement):")
    print(f"    banded : {per_year*t_fast/reps:6.2f} s")
    print(f"    dense  : {per_year*t_dense/reps:6.2f} s")
    print(f"    saved  : {per_year*(t_dense-t_fast)/reps:6.2f} s per year")

    ok = worst_diff < 1e-9 and worst_res_fast < 1e-9
    print("\n" + ("PASS - same system, same answer" if ok else "FAIL - investigate"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
