"""
src/surrogate/model_zoo.py
=============================
The surrogate candidates compared per regime x PCM pair, behind one
interface, plus the cross-validated bake-off that picks the per-pair
winner.

WHY XGBOOST IS DEMOTED TO "BASELINE" (the review comment that XGBoost is
too easy is correct, and for a stronger reason than novelty)
--------------------------------------------------------------------
This surrogate's job is to rank candidate designs over a SMOOTH, 3-input
response surface from ~128 Sobol points per pair, and to hand NSGA-II and
the active-learning loop something they can actually use. Gradient-boosted
trees are a poor structural match for that job:

  * They are piecewise-CONSTANT. The fitted surface is a staircase, so it
    has zero gradient almost everywhere and a search driven by it stalls
    on plateaus -- while the real response (energy vs. capsule diameter,
    flow, count) is smooth and differentiable.
  * They cannot extrapolate past the convex hull of the training data at
    all (a leaf prediction is constant outside it), which is exactly what
    the box-vertex and widened-bounds diagnostics probe.
  * They have no principled predictive variance. Active learning needs
    "where is the model unsure?", and a tree ensemble's spread is a
    heuristic, not a posterior.
  * At n~128 in 3 dimensions they are data-starved; boosting's advantage
    shows up at large n with many interacting features, neither of which
    applies here.

GAUSSIAN-PROCESS (KRIGING) REGRESSION IS THE RIGHT INSTRUMENT, and is
also the more advanced one. It is the standard surrogate in design
optimization for precisely this regime (low dimension, small smooth
dataset, uncertainty needed) -- the basis of Efficient Global Optimization
and Bayesian optimization. Concretely:

  * Smooth and differentiable by construction (Matern nu=5/2 gives
    twice-differentiable draws), so the optimizer sees real gradients.
  * An EXACT closed-form posterior standard deviation at every point,
    which replaces the ad-hoc "committee disagreement" heuristic in the
    active-learning loop with a calibrated uncertainty.
  * Anisotropic length scales are LEARNED per input dimension by
    marginal-likelihood maximization, which doubles as a sensitivity
    readout: a long length scale means that design variable barely
    matters, and that can be cross-checked directly against the Taguchi
    ANOVA contributions computed independently.
  * Interpolates its training points exactly (up to the fitted noise
    term), so a simulator run already spent is never contradicted by the
    surrogate.

All four candidates are still FITTED AND SCORED on every pair, XGBoost
included, so the demotion is a measured result reported in the registry
rather than an assertion -- same spirit as Rajasthan's per-pair winner
selection, with a stronger candidate set.

SELECTION CRITERION (fixed before seeing results, so it cannot be fitted
to the outcome): K-fold CV, winner = highest Spearman rank correlation,
with RMSE/sd(y) as the tie-break at equal Spearman within 0.01. Spearman
leads because this surrogate's actual job is RANKING designs for the
optimizer, not predicting absolute kWh.
"""

from dataclasses import dataclass, field

import numpy as np
from scipy.stats import spearmanr
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

RANDOM_SEED = 20261028


class _BaseSurrogate:
    """fit/predict/predict_std, with inputs standardized internally so
    every candidate sees the same conditioning."""
    name = "base"
    supports_exact_std = False

    def __init__(self):
        self._x_scaler = StandardScaler()
        self._fitted = False

    def _fit_scaler(self, X):
        return self._x_scaler.fit_transform(np.asarray(X, dtype=float))

    def _scale(self, X):
        return self._x_scaler.transform(np.asarray(X, dtype=float))

    def fit(self, X, y):
        raise NotImplementedError

    def predict(self, X):
        raise NotImplementedError

    def predict_std(self, X):
        raise NotImplementedError


class KrigingGP(_BaseSurrogate):
    """Anisotropic Matern-5/2 Gaussian process with a fitted noise term.

    nu=5/2 (not the RBF default) because RBF assumes infinitely smooth
    responses, which over-smooths near the melt-band transition where the
    response genuinely kinks; Matern-5/2 is twice differentiable --
    smooth enough for gradients, not so smooth that it ignores structure.
    The WhiteKernel absorbs the simulator's own small numerical scatter
    so the GP is not forced to interpolate solver noise.
    """
    name = "kriging_gp"
    supports_exact_std = True

    def __init__(self, n_restarts: int = 8, seed: int = RANDOM_SEED):
        super().__init__()
        self.n_restarts = n_restarts
        self.seed = seed
        self.model = None

    def fit(self, X, y):
        Xs = self._fit_scaler(X)
        y = np.asarray(y, dtype=float)
        d = Xs.shape[1]
        # Upper length-scale bound is deliberately generous (1e4 in
        # standardized units): a design variable the response does not
        # actually depend on wants an effectively infinite length scale,
        # and a tight bound turns that correct answer into a convergence
        # warning on every fit. A fitted length scale at/near the ceiling
        # is the readout for "this input is irrelevant", not a failure.
        kernel = (ConstantKernel(1.0, (1e-3, 1e3))
                  * Matern(length_scale=np.ones(d), length_scale_bounds=(1e-2, 1e4), nu=2.5)
                  + WhiteKernel(noise_level=1e-4, noise_level_bounds=(1e-10, 1e0)))
        self.model = GaussianProcessRegressor(
            kernel=kernel, normalize_y=True, n_restarts_optimizer=self.n_restarts,
            random_state=self.seed)
        self.model.fit(Xs, y)
        self._fitted = True
        return self

    def predict(self, X):
        return self.model.predict(self._scale(X))

    def predict_std(self, X):
        _, std = self.model.predict(self._scale(X), return_std=True)
        return std

    def length_scales(self):
        """Learned per-input length scales (in standardized units): LARGE
        means that design variable matters little. Cross-checkable against
        the Taguchi ANOVA contributions."""
        for part in [self.model.kernel_.k1, self.model.kernel_]:
            ls = getattr(getattr(part, "k2", None), "length_scale", None)
            if ls is not None:
                return np.atleast_1d(ls)
        return None


class QuadraticRSM(_BaseSurrogate):
    """Classical second-order response surface (full quadratic + two-way
    interactions) with ridge regularization. The interpretable benchmark:
    if a quadratic wins, the response really is bowl-shaped and no
    flexible model is warranted."""
    name = "quadratic_rsm"

    def __init__(self):
        super().__init__()
        self.model = None
        self._resid_sd = 0.0

    def fit(self, X, y):
        Xs = self._fit_scaler(X)
        y = np.asarray(y, dtype=float)
        self.model = make_pipeline(
            PolynomialFeatures(degree=2, include_bias=False),
            RidgeCV(alphas=np.logspace(-6, 3, 40)))
        self.model.fit(Xs, y)
        self._resid_sd = float(np.std(y - self.model.predict(Xs)))
        self._fitted = True
        return self

    def predict(self, X):
        return self.model.predict(self._scale(X))

    def predict_std(self, X):
        # Homoscedastic by construction -- reported as a flat residual sd
        # rather than dressed up as a posterior. A caller doing active
        # learning on this model gets no spatial information, which is
        # itself a reason to prefer the GP for that role.
        return np.full(len(np.asarray(X)), self._resid_sd)


class NNEnsemble(_BaseSurrogate):
    """Five 2x32 tanh MLPs with different initializations (the ensemble
    Rajasthan's report uses). Mean = prediction, across-member spread =
    uncertainty."""
    name = "nn_ensemble"

    def __init__(self, n_members: int = 5, hidden=(32, 32), seed: int = RANDOM_SEED):
        super().__init__()
        self.n_members = n_members
        self.hidden = hidden
        self.seed = seed
        self.members = []
        self._y_mean = 0.0
        self._y_sd = 1.0

    def fit(self, X, y):
        Xs = self._fit_scaler(X)
        y = np.asarray(y, dtype=float)
        self._y_mean, self._y_sd = float(np.mean(y)), float(np.std(y)) or 1.0
        yz = (y - self._y_mean) / self._y_sd
        self.members = []
        for k in range(self.n_members):
            m = MLPRegressor(hidden_layer_sizes=self.hidden, activation="tanh",
                             solver="lbfgs", max_iter=5000, tol=1e-8,
                             alpha=1e-4, random_state=self.seed + k)
            m.fit(Xs, yz)
            self.members.append(m)
        self._fitted = True
        return self

    def _member_preds(self, X):
        Xs = self._scale(X)
        return np.stack([m.predict(Xs) for m in self.members], axis=0)

    def predict(self, X):
        return self._member_preds(X).mean(axis=0) * self._y_sd + self._y_mean

    def predict_std(self, X):
        return self._member_preds(X).std(axis=0) * self._y_sd


class GBTBaseline(_BaseSurrogate):
    """XGBoost, kept as the baseline the others are measured against (see
    module docstring for why it is not the production choice)."""
    name = "xgboost_baseline"

    def __init__(self, seed: int = RANDOM_SEED):
        super().__init__()
        self.seed = seed
        self.model = None

    def fit(self, X, y):
        from xgboost import XGBRegressor
        Xs = self._fit_scaler(X)
        self.model = XGBRegressor(n_estimators=400, max_depth=3, learning_rate=0.05,
                                   subsample=0.9, colsample_bytree=1.0,
                                   reg_lambda=1.0, random_state=self.seed,
                                   n_jobs=1, verbosity=0)
        self.model.fit(Xs, np.asarray(y, dtype=float))
        self._fitted = True
        return self

    def predict(self, X):
        return self.model.predict(self._scale(X))

    def predict_std(self, X):
        # No principled posterior exists for a boosted-tree point
        # prediction; returning NaN is the honest answer and makes any
        # attempt to drive active learning from this model fail loudly
        # instead of silently using a meaningless number.
        return np.full(len(np.asarray(X)), np.nan)


def all_candidates(seed: int = RANDOM_SEED):
    return [KrigingGP(seed=seed), QuadraticRSM(), NNEnsemble(seed=seed), GBTBaseline(seed=seed)]


@dataclass
class CVScore:
    model: str
    spearman: float
    rmse: float
    rmse_over_sd: float
    mae: float
    r2: float
    fit_seconds: float
    std_calibration: float = float("nan")   # fraction of truths inside +/-2 sd (target ~0.95)
    extras: dict = field(default_factory=dict)


def cross_validate(model_factory, X, y, n_splits: int = 5, seed: int = RANDOM_SEED) -> CVScore:
    """K-fold CV producing out-of-fold predictions, then scores computed
    once on the full out-of-fold vector (not averaged per fold -- a
    Spearman averaged over small folds is not the Spearman of the ranking
    the optimizer actually sees)."""
    import time
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    kf = KFold(n_splits=min(n_splits, len(y)), shuffle=True, random_state=seed)
    oof = np.full(len(y), np.nan)
    oof_std = np.full(len(y), np.nan)
    t0 = time.perf_counter()
    for tr, te in kf.split(X):
        m = model_factory().fit(X[tr], y[tr])
        oof[te] = m.predict(X[te])
        try:
            oof_std[te] = m.predict_std(X[te])
        except Exception:
            pass
    fit_s = time.perf_counter() - t0

    resid = y - oof
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    sd_y = float(np.std(y)) or 1.0
    rho = float(spearmanr(y, oof).statistic) if len(np.unique(y)) > 2 else float("nan")
    ss_tot = float(np.sum((y - np.mean(y)) ** 2)) or 1.0
    cal = (float(np.mean(np.abs(resid) <= 2.0 * oof_std)) if np.isfinite(oof_std).all()
           else float("nan"))
    name = model_factory().name
    return CVScore(model=name, spearman=rho, rmse=rmse, rmse_over_sd=rmse / sd_y,
                   mae=float(np.mean(np.abs(resid))), r2=1.0 - float(np.sum(resid ** 2)) / ss_tot,
                   fit_seconds=fit_s, std_calibration=cal)


def bake_off(X, y, n_splits: int = 5, seed: int = RANDOM_SEED, factories=None):
    """Scores every candidate and returns (winner_name, [CVScore, ...]).

    Winner = highest Spearman; if two are within 0.01 Spearman, the lower
    RMSE/sd(y) wins. Criterion fixed in the module docstring before any
    results were seen.
    """
    factories = factories or [lambda: KrigingGP(seed=seed), QuadraticRSM,
                              lambda: NNEnsemble(seed=seed), lambda: GBTBaseline(seed=seed)]
    scores = [cross_validate(f, X, y, n_splits=n_splits, seed=seed) for f in factories]
    best = max(scores, key=lambda s: (round(s.spearman, 2), -s.rmse_over_sd))
    ties = [s for s in scores if abs(s.spearman - best.spearman) <= 0.01]
    winner = min(ties, key=lambda s: s.rmse_over_sd)
    return winner.model, scores
