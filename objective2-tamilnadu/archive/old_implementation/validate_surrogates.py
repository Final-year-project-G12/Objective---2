"""Validation for src/surrogate/model_zoo.py, on synthetic responses whose
answers are known in advance, before any of it is pointed at real DOE data.

Three claims are tested, each of which the module's docstring makes and
the active-learning loop depends on:

  1. On a SMOOTH 3-input response at the real Sobol budget (n=128), the
     Gaussian process ranks designs better than the gradient-boosted-tree
     baseline. (The docstring's structural argument; if it is wrong, the
     argument is wrong.)
  2. The GP's posterior standard deviation is CALIBRATED -- about 95% of
     held-out truths fall inside +/-2 sigma. Active learning samples where
     sigma is large, so an uncalibrated sigma sends it to the wrong places.
  3. The GP's learned anisotropic length scales identify which inputs
     matter. Tested by including a genuinely IRRELEVANT third variable and
     checking the GP gives it a much longer length scale -- which is what
     licenses cross-checking length scales against the Taguchi ANOVA.

The test function is a stand-in for the real response's shape (saturating
in one variable, curved in another, flat in a third), NOT a physics model.
"""

import numpy as np
from scipy.stats import qmc

from src.surrogate.model_zoo import (KrigingGP, QuadraticRSM, NNEnsemble, GBTBaseline,
                                     cross_validate, bake_off)

N_TRAIN = 128          # the per-pair Sobol budget
SEED = 20261028
rng = np.random.default_rng(SEED)


def smooth_response(X):
    """Saturating in x0, curved with an interaction in x1, FLAT in x2."""
    x0, x1 = X[:, 0], X[:, 1]
    return 10.0 * (1.0 - np.exp(-3.0 * x0)) + 4.0 * x1 ** 2 - 2.5 * x0 * x1 + 1.0


X = qmc.Sobol(d=3, scramble=True, seed=SEED).random(N_TRAIN)
y_clean = smooth_response(X)
noise_sd = 0.01 * float(np.std(y_clean))
y = y_clean + rng.normal(0.0, noise_sd, N_TRAIN)

print(f"synthetic smooth response, n={N_TRAIN}, 3 inputs (x2 irrelevant), "
      f"noise = 1% of sd(y)\n")

winner, scores = bake_off(X, y, n_splits=5, seed=SEED)
print(f"{'model':20s} {'spearman':>10s} {'rmse/sd':>10s} {'r2':>8s} {'+/-2sd cover':>14s} {'fit s':>8s}")
print("-" * 76)
for s in sorted(scores, key=lambda s: -s.spearman):
    cov = "n/a" if s.std_calibration != s.std_calibration else f"{s.std_calibration:.3f}"
    print(f"{s.model:20s} {s.spearman:10.5f} {s.rmse_over_sd:10.5f} {s.r2:8.4f} "
          f"{cov:>14s} {s.fit_seconds:8.2f}")
print(f"\nwinner by the fixed criterion: {winner}")

by_name = {s.model: s for s in scores}
gp, gbt = by_name["kriging_gp"], by_name["xgboost_baseline"]

# ---- claim 1: GP beats the tree baseline on a smooth low-dim response
print(f"\nGP vs XGBoost:  spearman {gp.spearman:.5f} vs {gbt.spearman:.5f}   "
      f"rmse/sd {gp.rmse_over_sd:.5f} vs {gbt.rmse_over_sd:.5f}  "
      f"({gbt.rmse_over_sd / gp.rmse_over_sd:.1f}x more error)")
assert gp.spearman > gbt.spearman, "GP did not out-rank the tree baseline on a smooth response"
assert gp.rmse_over_sd < gbt.rmse_over_sd, "GP did not beat the tree baseline on RMSE"

# ---- claim 2: the GP's sigma is calibrated
print(f"GP +/-2sd coverage: {gp.std_calibration:.3f} (target ~0.95)")
assert 0.85 <= gp.std_calibration <= 1.0, \
    f"GP posterior sd is not calibrated (coverage {gp.std_calibration:.3f})"

# ---- claim 3: length scales find the irrelevant variable
m = KrigingGP(seed=SEED).fit(X, y)
ls = m.length_scales()
print(f"\nGP learned length scales (standardized units): {np.round(ls, 3)}")
print("  (x0, x1 are real; x2 is pure noise -- its length scale should be much longer)")
assert ls is not None and len(ls) == 3, "could not read back per-dimension length scales"
assert ls[2] > 3.0 * max(ls[0], ls[1]), \
    f"GP did not identify the irrelevant input: length scales {ls}"

# ---- the quadratic should do WELL here (the response is nearly quadratic),
# which is the point of keeping it: it is a real contender, not a straw man.
quad = by_name["quadratic_rsm"]
print(f"\nquadratic RSM spearman {quad.spearman:.5f} -- a genuine contender on a "
      f"near-quadratic response, which is why it stays in the bake-off")

print("\nPASS: GP out-ranks and out-predicts the tree baseline, its posterior sd is "
      "calibrated,\n      and its length scales correctly flag the irrelevant input.")
