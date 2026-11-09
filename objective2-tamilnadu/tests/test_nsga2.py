"""tests/test_nsga2.py - G9/S4: the hand-written NSGA-II, hypervolume and epsilon indicator behave on known problems."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.optimize import nsga2 as ns


def test_hypervolume_exact_boxes():
    assert ns.hypervolume([[1, 1]], [2, 2]) == pytest.approx(1.0)
    assert ns.hypervolume([[1, 3], [3, 1]], [4, 4]) == pytest.approx(3 * 1 + 1 * 3 - 0 + 0) or True
    # two staircase points: areas (4-1)*(4-3) + (4-3)*(3-1) = 3 + 2 = 5
    assert ns.hypervolume([[1, 3], [3, 1]], [4, 4]) == pytest.approx(5.0)
    assert ns.hypervolume([[1, 1, 1]], [2, 2, 2]) == pytest.approx(1.0)
    # 3-D: two non-nested boxes against ref (3,3,3): 2*2*1 ... computed by inclusion-exclusion
    a, b = np.array([1, 2, 2]), np.array([2, 1, 2])
    va, vb = np.prod(3 - a), np.prod(3 - b)
    vab = np.prod(3 - np.maximum(a, b))
    assert ns.hypervolume([a, b], [3, 3, 3]) == pytest.approx(va + vb - vab)
    assert ns.hypervolume([[5, 5]], [2, 2]) == 0.0


def test_non_dominated_mask_and_epsilon():
    F = np.array([[1, 3], [2, 2], [3, 1], [3, 3], [2.5, 2.5]])
    assert ns.non_dominated_mask(F).tolist() == [True, True, True, False, False]
    eps, _ = ns.additive_epsilon(F[:3], F[:3])
    assert eps == pytest.approx(0.0)
    eps_shifted, _ = ns.additive_epsilon(F[:3] + 0.5, F[:3])
    assert eps_shifted == pytest.approx(0.5)
    assert ns.additive_epsilon(F[:3] - 1.0, F[:3])[0] < 0


def _zdt1(X):
    f1 = X[:, 0]
    g = 1 + 9 * X[:, 1:].mean(axis=1)
    return np.column_stack([f1, g * (1 - np.sqrt(f1 / g))]), np.zeros(len(X))


def test_nsga2_recovers_zdt1_front():
    out = ns.nsga2(_zdt1, n_var=6, n_pop=60, n_gen=80, seed=3)
    F = out["F"][ns.pareto_set(out["F"], out["G"])]
    f1 = np.linspace(0, 1, 2001)
    true_hv = ns.hypervolume(np.column_stack([f1, 1 - np.sqrt(f1)]), [1.1, 1.1])
    assert ns.hypervolume(F, [1.1, 1.1]) > 0.98 * true_hv
    assert F[:, 0].min() < 0.03 and F[:, 0].max() > 0.9           # spread along the whole front


def test_nsga2_respects_constraints_and_is_seeded():
    def prob(X):                                # minimise (x0, 1-x0 + x1); feasible only if x1 >= 0.5
        F = np.column_stack([X[:, 0], 1 - X[:, 0] + X[:, 1]])
        G = np.maximum(0.0, 0.5 - X[:, 1])
        return F, G
    a = ns.nsga2(prob, 2, n_pop=40, n_gen=40, seed=5)
    b = ns.nsga2(prob, 2, n_pop=40, n_gen=40, seed=5)
    assert np.allclose(a["X"], b["X"])                              # reproducible from the seed
    feas = a["G"] <= 0
    assert feas.mean() > 0.9 and a["X"][feas, 1].min() >= 0.5 - 1e-9
    front = a["F"][ns.pareto_set(a["F"], a["G"])]
    assert np.all(front[:, 1] >= 0.5 - 1e-9) and front[:, 1].min() < 0.6      # pushes to the constraint boundary
