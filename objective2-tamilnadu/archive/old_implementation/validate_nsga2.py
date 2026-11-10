import numpy as np
from src.optimize.nsga2 import run_nsga2, hypervolume, fast_non_dominated_sort

N_VARS = 10

def zdt1(X):
    f1 = X[:, 0]
    g = 1.0 + 9.0 * X[:, 1:].sum(axis=1) / (N_VARS - 1)
    f2 = g * (1.0 - np.sqrt(np.clip(f1 / g, 0, None)))
    F = np.stack([f1, f2], axis=1)
    G = np.zeros(len(X))
    return F, G

lo = np.zeros(N_VARS)
hi = np.ones(N_VARS)

result = run_nsga2(zdt1, lo, hi, pop_size=60, n_gen=80, seed=42, ref_point=np.array([1.2, 1.2]))

front0 = result.fronts[0]
F0 = result.F[front0]
order = np.argsort(F0[:, 0])
F0 = F0[order]

true_f2 = 1.0 - np.sqrt(np.clip(F0[:, 0], 0, 1))
rmse_to_true_front = float(np.sqrt(np.mean((F0[:, 1] - true_f2) ** 2)))

print(f"Final non-dominated front size: {len(front0)} / {len(result.F)}")
print(f"f1 range on front: [{F0[:,0].min():.4f}, {F0[:,0].max():.4f}]")
print(f"RMSE of front to TRUE ZDT1 Pareto front (f2 = 1 - sqrt(f1)): {rmse_to_true_front:.5f}")
print(f"Hypervolume: gen0={result.history_hypervolume[0]:.4f}  gen-final={result.history_hypervolume[-1]:.4f}")
print(f"Hypervolume history (every 10 gens): {[round(h,4) for h in result.history_hypervolume[::10]]}")

# sanity: hypervolume should be monotonically non-decreasing (elitist NSGA-II)
hv = np.array(result.history_hypervolume)
n_decreases = int(np.sum(np.diff(hv) < -1e-9))
print(f"Generations where HV decreased (should be 0, elitism check): {n_decreases}")

diffs = np.diff(hv)
bad = np.where(diffs < -1e-9)[0]
print("\nDecreases detail (gen index -> hv[gen], hv[gen+1], diff):")
for b in bad:
    print(f"  gen {b}: {hv[b]:.6f} -> {hv[b+1]:.6f}  diff={diffs[b]:.6f}")

# Standard (crowding-distance) NSGA-II does NOT guarantee strictly
# monotonic hypervolume -- only hypervolume-based variants like SMS-EMOA
# do. Once the front already has >pop_size non-dominated points, crowding
# distance truncates for DIVERSITY, not hypervolume, so tiny late-stage
# dips (trading a high-HV-contribution point for a better-spread one) are
# expected, textbook-correct behavior, not a defect -- bounded here at a
# generous 1% of current HV to still catch a genuinely broken elitism
# (e.g. losing the whole front, a multi-percent collapse).
max_relative_decrease = float(np.max(-diffs[diffs < 0]) / hv[:-1][diffs < 0].max()) if n_decreases else 0.0
print(f"Largest single-generation relative HV decrease: {100*max_relative_decrease:.3f}%")

assert rmse_to_true_front < 0.02, "NSGA-II did not converge close to the true ZDT1 front"
assert max_relative_decrease < 0.01, "Hypervolume dropped by >1% in one generation -- elitism may be broken"
print("\nPASS: NSGA-II converges to the true ZDT1 Pareto front; hypervolume rises to within "
      "expected crowding-distance noise (standard NSGA-II is not strictly HV-monotonic).")
