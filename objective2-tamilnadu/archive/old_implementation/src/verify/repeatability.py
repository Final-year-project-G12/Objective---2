"""
src/verify/repeatability.py
==============================
The repeatability band: how big a difference in the primary objective has
to be before it means anything.

Her report builds the band by combining the effects that move a number
without the DESIGN changing at all, then requires any claimed win to clear
it ("It is far above the repeatability band (14-22 kWh) in every regime
and every test year"). The four contributions she lists:

  year     weather year to weather year, same design
  dt       solver timestep (her "dt 150 vs 75")
  node     node count (her "N = 10 vs 20 changes the paired gain by
           0.15-0.25 pp; part of the band")
  property PCM property uncertainty (conductivity / latent heat)

Combined in quadrature, not added: these are independent perturbations, so
the band is sqrt(sum of squares). Summing them would overstate the band
and let real differences be dismissed as noise; taking only the largest
would understate it.

Every term is MEASURED on the chosen designs by re-simulating them with
one thing perturbed at a time -- the band is not a guess or a literature
value.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.parallel.runner import SimTask, run_tasks_parallel

OBJECTIVE = "g_window_kWh"


@dataclass
class BandBreakdown:
    cluster_id: int
    year_term: float
    dt_term: float
    node_term: float
    property_term: float
    band_kWh: float

    def as_row(self):
        return {
            "cluster_id": self.cluster_id,
            "year_sd_kWh": self.year_term,
            "dt_effect_kWh": self.dt_term,
            "node_effect_kWh": self.node_term,
            "property_effect_kWh": self.property_term,
            "band_kWh": self.band_kWh,
        }


def _task(design, state, cid, year, *, n_nodes=10, dt=150.0, overrides=(), tag=""):
    return SimTask(
        task_id=f"{tag}_c{cid}_y{year}_n{n_nodes}_dt{dt:g}",
        state=state, cluster_id=cid, pcm_name=design["pcm_name"],
        capsule_diameter_m=float(design["capsule_diameter_m"]),
        n_capsule=int(design["n_capsule"]),
        flow_rate_kg_s=float(design["flow_rate_kg_s"]),
        arrangement=design["arrangement"],
        model="multinode", n_nodes=n_nodes, timestep_s=dt, year=year,
        paired_plain=True, pcm_property_overrides=tuple(overrides))


def measure_band(designs: pd.DataFrame, state: str, years, base_dt: float = 150.0,
                  base_nodes: int = 10, fine_dt: float = 75.0, more_nodes: int = 20,
                  property_deltas=(("TC_W_mK", 0.85), ("latent_heat_kJ_kg", 0.90)),
                  verbose: bool = True):
    """designs: one row per regime (the chosen design). Returns
    (DataFrame of band rows, DataFrame of every run behind it)."""
    tasks, meta = [], []

    for _, d in designs.iterrows():
        cid = int(d["cluster_id"])
        # year term: base config, every year
        for y in years:
            tasks.append(_task(d, state, cid, y, n_nodes=base_nodes, dt=base_dt, tag="base"))
            meta.append((cid, "base", y))
        # dt term and node term: one reference year each
        y0 = years[0]
        tasks.append(_task(d, state, cid, y0, n_nodes=base_nodes, dt=fine_dt, tag="finedt"))
        meta.append((cid, "finedt", y0))
        tasks.append(_task(d, state, cid, y0, n_nodes=more_nodes, dt=base_dt, tag="nodes"))
        meta.append((cid, "nodes", y0))
        # property term: one perturbation per property, reference year
        for k, mult in property_deltas:
            from src.io_utils import get_pcm_properties
            base_val = float(get_pcm_properties(state, d["pcm_name"])[k])
            tasks.append(_task(d, state, cid, y0, n_nodes=base_nodes, dt=base_dt,
                               overrides=((k, base_val * mult),), tag=f"prop_{k}"))
            meta.append((cid, f"prop_{k}", y0))

    df = run_tasks_parallel(tasks, chunksize=2, progress_every=max(1, len(tasks) // 10),
                            label="repeatability")
    df["_kind"] = [m[1] for m in meta]
    df["_cid"] = [m[0] for m in meta]

    rows = []
    for cid, g in df[df["valid"]].groupby("_cid"):
        base = g[g["_kind"] == "base"][OBJECTIVE]
        base_ref = float(base.iloc[0]) if len(base) else float("nan")
        year_term = float(base.std(ddof=1)) if len(base) > 1 else 0.0

        def delta(kind):
            sub = g[g["_kind"] == kind][OBJECTIVE]
            return abs(float(sub.iloc[0]) - base_ref) if len(sub) else 0.0

        dt_term = delta("finedt")
        node_term = delta("nodes")
        prop_terms = [delta(k) for k in g["_kind"].unique() if str(k).startswith("prop_")]
        prop_term = float(np.sqrt(np.sum(np.square(prop_terms)))) if prop_terms else 0.0

        band = float(np.sqrt(year_term**2 + dt_term**2 + node_term**2 + prop_term**2))
        bb = BandBreakdown(int(cid), year_term, dt_term, node_term, prop_term, band)
        rows.append(bb.as_row())
        if verbose:
            print(f"  regime {cid}: year={year_term:6.2f} dt={dt_term:6.2f} "
                  f"node={node_term:6.2f} prop={prop_term:6.2f} -> band={band:6.2f} kWh",
                  flush=True)

    return pd.DataFrame(rows), df
