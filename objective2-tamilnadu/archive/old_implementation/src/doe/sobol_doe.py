"""
src/doe/sobol_doe.py
=======================
Sobol-sequence DOE, ported from Manvitha's Rajasthan report ("G8 S2":
"128 scrambled-Sobol points, seed 20261026, same points for every pair,
5 explore years"). ADDITIVE to src/doe/generate_cases.py's existing
LHS+boundary plan, which stays exactly as-is and is still what Phase 5's
current, validated output uses -- this is the new sampling method for the
NSGA-II/active-learning/3-way-surrogate chain specifically.

Scrambled Sobol (quasi-random, low-discrepancy) covers the design space
more evenly than Latin Hypercube at a given sample count -- this is why
Rajasthan's report uses it for the larger (128-point) DOE that trains the
surrogates, while keeping LHS for quick boundary/screening use.

Design variables (the v3.0 search space, read from
configs/design_bounds_shared.yaml so every sampler agrees about the legal
ranges):
  capsule_diameter_m, flow_rate_kg_s, pcm_volume_fraction

pcm_volume_fraction replaced capsule_count as the third variable in config
v3.0 -- matching the Rajasthan study's own parameterization ("PCM
outer-volume fraction of the tank; capsule count N is derived", her
Table 2). Sampling the fraction keeps the sequence's low-discrepancy
property on a quantity that is physically meaningful and dimensionless;
the integer capsule count is DERIVED afterwards
(src/design/volume_fraction.py), so the rounding lands on the derived
quantity rather than on a searched one.

"Same points for every pair": the Sobol sequence itself (in [0,1)^3) is
generated ONCE with a fixed seed and reused unchanged for every regime x
PCM x arrangement pair -- only the final scaling to each pair's bounds
differs (bounds are currently pair-independent in this project, so in
practice the scaled points are identical across pairs too; the shared
[0,1)^3 sequence is kept regardless, matching the report's intent, in case
a future state ever has pair-specific bounds).
"""

from dataclasses import dataclass

import numpy as np

from src.io_utils import load_state_config, load_design_bounds

SOBOL_SEED = 20261026   # fixed, matches Rajasthan's own documented seed choice
N_SOBOL_POINTS = 128


@dataclass
class SobolCaseSpec:
    case_id: str
    regime_id: int
    pcm_id: object
    capsule_diameter_m: float
    pcm_volume_fraction: float      # SEARCHED (v3.0); capsule count is derived from it
    flow_rate_kg_s: float
    capsule_arrangement: str
    sampling_method: str = "sobol"
    seed: int = SOBOL_SEED


def _sobol_unit_points(n_points: int, seed: int = SOBOL_SEED) -> np.ndarray:
    # scipy.stats imported HERE, not at module scope: `import scipy.stats`
    # costs ~4.6 s and every spawned worker re-imports this module
    # (Windows spawn re-imports __main__), while only the parent ever
    # generates the sequence.
    from scipy.stats import qmc
    """The ONE shared [0,1)^3 scrambled-Sobol sequence, generated once.
    scipy requires n_points to be a power of 2 for the balance guarantee of
    a scrambled Sobol sequence to hold exactly; 128 = 2**7 already is."""
    sampler = qmc.Sobol(d=3, scramble=True, seed=seed)
    return sampler.random(n=n_points)


def generate_sobol_cases(state: str, n_points: int = N_SOBOL_POINTS):
    """Returns (list_of_SobolCaseSpec, manifest_dict) -- one Sobol DOE
    stratified by arrangement, covering every (regime, PCM, arrangement)
    triple, exactly mirroring generate_cases.py's existing stratification
    rule (every pair must see all 3 arrangements, or the surrogate/ANOVA
    would see "staggered" far more often than "radial")."""
    cfg = load_state_config(state)
    bounds = load_design_bounds()
    arrangements = bounds["capsule_arrangement"]["allowed"]

    d_bounds = bounds["capsule_diameter_m"]
    f_bounds = bounds["flow_rate_kg_s"]
    v_bounds = bounds["pcm_volume_fraction"]

    from scipy.stats import qmc
    unit = _sobol_unit_points(n_points)   # shared across every pair, as documented above
    diam = qmc.scale(unit[:, [0]], [d_bounds["min"]], [d_bounds["max"]]).ravel()
    flow = qmc.scale(unit[:, [1]], [f_bounds["min"]], [f_bounds["max"]]).ravel()
    frac = qmc.scale(unit[:, [2]], [v_bounds["min"]], [v_bounds["max"]]).ravel()

    all_cases = []
    n_pairs = 0
    for regime in cfg["regimes"]:
        cid = regime["cluster_id"]
        for pcm_id in regime["pcm_shortlist"]:
            n_pairs += 1
            prefix = f"c{cid}_{_slug(pcm_id)}_sobol"
            for arrangement in arrangements:
                for i in range(n_points):
                    all_cases.append(SobolCaseSpec(
                        case_id=f"{prefix}_{arrangement}_{i:03d}",
                        regime_id=cid, pcm_id=pcm_id,
                        capsule_diameter_m=float(diam[i]),
                        pcm_volume_fraction=float(frac[i]),
                        flow_rate_kg_s=float(flow[i]), capsule_arrangement=arrangement,
                    ))

    manifest = {
        "state": state, "sobol_seed": SOBOL_SEED, "n_points_per_pair_per_arrangement": n_points,
        "n_regime_pcm_pairs": n_pairs, "arrangements": arrangements,
        "n_total_cases": len(all_cases), "design_bounds_version": bounds.get("version"),
    }
    return all_cases, manifest


def _slug(name):
    return "".join(c if c.isalnum() else "_" for c in str(name))[:24]


if __name__ == "__main__":
    import sys
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    cases, manifest = generate_sobol_cases(state)
    print(f"Generated {manifest['n_total_cases']} Sobol DOE cases for state={state}:")
    print(f"  {manifest['n_regime_pcm_pairs']} regime x PCM pairs x {len(manifest['arrangements'])} "
          f"arrangements x {manifest['n_points_per_pair_per_arrangement']} points")
    print(f"  seed = {manifest['sobol_seed']}")
