"""
scripts/g12_registry.py
==========================
G12 - results registry. Every headline number quoted in docs/ is a row here: quantity, value, unit, the saved file it
was read from and the filter that selects it. The script only READS files under results/ and writes
results/results_registry.csv; nothing is computed from memory, so a number that is not in this table has no saved source.
Usage: python scripts/g12_registry.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.weather.inventory import REGIMES

OUT = Path("results")
ROWS = []


def add(rid, quantity, value, unit, source, flt=""):
    ROWS.append({"id": rid, "quantity": quantity, "value": value, "unit": unit, "source_file": f"results/{source}",
                 "filter": flt})


def main():
    # --- WP6 repeatability band (all regimes pooled and per regime)
    band = pd.read_csv(OUT / "wp6_band.csv")
    for r in band.itertuples():
        add(f"band.{r.scope}.{r.objective}", f"WP6 repeatability band ({r.scope}, {r.objective})", round(r.band, 3),
            "h" if r.objective == "d_overheat" else "kWh", "wp6_band.csv", f"scope={r.scope}, objective={r.objective}")

    # --- G10 selection (select years 2021-2023)
    for c in REGIMES:
        j = json.loads((OUT / f"g10_selection_r{c}.json").read_text(encoding="utf-8"))
        k = j["chosen"]
        src = f"g10_selection_r{c}.json"
        add(f"sel.r{c}.pcm", f"regime {c} chosen PCM", k["pcm"], "", src, "chosen")
        for key, unit, nd in (("R_in_m", "m", 4), ("fraction", "-", 4), ("N", "capsules", 0), ("flow", "kg/s", 4),
                              ("g_window", "kWh/yr", 2), ("g_annual", "kWh/yr", 2), ("d_overheat", "h/yr", 1),
                              ("t_pcm_max", "C", 2), ("t_water_max", "C", 2), ("pcm_mass_kg", "kg", 3)):
            v = k[key]
            add(f"sel.r{c}.{key}", f"regime {c} chosen design: {key} (select years, paired vs same-flow water-only)",
                round(float(v), nd) if nd else int(v), unit, src, "chosen")
        add(f"sel.r{c}.arrangement", f"regime {c} chosen arrangement", k["arrangement"], "", src, "chosen")
        if "gain_tau_serve_h" in k:
            add(f"sel.r{c}.gain_tau_serve_h", f"regime {c} chosen design: tau_serve gain", round(float(k["gain_tau_serve_h"]), 3),
                "h", src, "chosen")
        add(f"sel.r{c}.nS0", f"regime {c} candidates indistinguishable on g_window (S0)", j["n_S0_indistinguishable_on_g_window"],
            "designs", src, "")
        add(f"sel.r{c}.band_g_window", f"regime {c} band used for g_window", round(j["band"]["g_window"], 2), "kWh", src, "band")

    # --- G10 held-out test
    h = pd.read_csv(OUT / "g10_heldout_results.csv")
    for r in h.itertuples():
        base = f"test.r{r.regime}.{r.role}.{r.pcm.replace(' ', '_')}.{r.year}"
        flt = f"regime={r.regime}, role={r.role}, pcm={r.pcm}, year={r.year}"
        for key, unit, nd in (("g_window", "kWh", 2), ("g_annual", "kWh", 2), ("d_overheat", "h", 1), ("t_pcm_max", "C", 2),
                              ("t_water_max", "C", 2), ("gain_tau_serve_mean_h", "h", 3)):
            add(f"{base}.{key}", f"held-out {key}", round(float(getattr(r, key)), nd), unit, "g10_heldout_results.csv", flt)

    # --- issue 4: shield hours split (scripts/g13_issue4_shield_split.py)
    sp = pd.concat([pd.read_csv(OUT / f"g13_shield_split_r{c}.csv") for c in REGIMES])
    for c in REGIMES:
        x = sp[(sp.regime == c) & (sp.role == "chosen") & (sp.purpose == "select")]
        for key, unit in (("shield_water_h_pcm", "h/yr"), ("shield_water_h_plain", "h/yr"), ("d_shield_water_h", "h/yr"),
                          ("shield_pcm_h", "h/yr"), ("d_overheat_as_stored", "h/yr"), ("t_water_max_pcm_C", "C"), ("t_water_max_plain_C", "C")):
            add(f"shield.r{c}.{key}", f"regime {c} chosen design, select-year mean: {key}", round(float(x[key].mean()), 1), unit,
                f"g13_shield_split_r{c}.csv", "role=chosen, purpose=select, mean of 2021-2023")
    add("shield.rows_with_fewer_water_side_hours", f"design-years ({sp.groupby(['regime', 'role', 'pcm']).ngroups} designs x 8 years) with fewer water-side shield hours than water-only",
        int((sp.d_shield_water_h < 0).sum()), f"of {len(sp)}", "g13_shield_split_r{0,1,2,3}.csv", "d_shield_water_h < 0")

    # --- issue 5: controls from an interior anchor (scripts/g14_issue5_controls.py)
    for c in REGIMES:
        d = pd.read_csv(OUT / f"g14_controls_r{c}.csv")
        base = float(d[d.block == "base"].g_window.iloc[0])
        add(f"ctrl.r{c}.anchor_g_window", f"regime {c} interior-anchor g_window (R25, 10 %, 0.030 kg/s)", round(base, 2), "kWh/yr", f"g14_controls_r{c}.csv", "block=base")
        for blk, lv in (("thickness_const_mass", "R10"), ("thickness_const_mass", "R15"), ("thickness_const_mass", "R20"),
                        ("thickness_const_mass", "R30"), ("thickness_const_mass", "R40"), ("fraction", "x0.5"), ("fraction", "x2")):
            v = float(d[(d.block == blk) & (d.level == lv)].g_window.iloc[0]) - base
            add(f"ctrl.r{c}.{blk}.{lv}", f"regime {c} change in g_window vs interior anchor: {blk} {lv}", round(v, 2), "kWh/yr",
                f"g14_controls_r{c}.csv", f"block={blk}, level={lv}, minus anchor")

    # --- issue 6: stack-anchor dependence (scripts/g15_issue6_anchor.py)
    an = pd.concat([pd.read_csv(OUT / f"g15_anchor_r{c}.csv") for c in REGIMES])
    sa = an[an.purpose == "select"].groupby(["regime", "role", "pcm", "anchor"]).g_window.mean().reset_index()
    for c in REGIMES:
        x = sa[(sa.regime == c) & (sa.role == "chosen")].set_index("anchor").g_window
        for a in ("bottom", "center", "top"):
            add(f"anchor.r{c}.chosen.{a}", f"regime {c} chosen design g_window with the stack at the {a} (select-year mean)", round(float(x[a]), 2),
                "kWh/yr", f"g15_anchor_r{c}.csv", f"role=chosen, purpose=select, anchor={a}")
        add(f"anchor.r{c}.chosen.range", f"regime {c} chosen design: g_window range over the three stack positions", round(float(x.max() - x.min()), 2),
            "kWh/yr", f"g15_anchor_r{c}.csv", "max - min over bottom/center/top")
    add("anchor.min_gain_any", "smallest explore/select-year mean g_window of any kept design at any stack position",
        round(float(an.groupby(["regime", "role", "pcm", "anchor", "purpose"]).g_window.mean().min()), 2), "kWh/yr", "g15_anchor_r{0,1,2,3}.csv",
        "min over the kept designs x 3 anchors x 2 year roles x 4 regimes")

    # --- issue 3: evening-scenario decomposition (scripts/g16_issue3_serve.py)
    sv = pd.concat([pd.read_csv(OUT / f"g16_serve_r{c}.csv") for c in REGIMES])    # Uttarakhand: plain_40L is in the main file (one run)
    sv = sv[sv.valid == True]  # noqa: E712
    sm = sv.groupby(["regime", "case"])[["tau_hold_mean_h", "tau_serve_mean_h", "serve_frac_45_mean", "serve_E_del45_mean_kWh"]].mean()
    for c in REGIMES:
        for case in ("pcm", "plain", "pcm_L0", "plain_40L"):
            for key, unit, nd in (("tau_serve_mean_h", "h", 3), ("serve_frac_45_mean", "-", 4), ("serve_E_del45_mean_kWh", "kWh/night", 3),
                                  ("tau_hold_mean_h", "h", 2)):
                add(f"serve.r{c}.{case}.{key}", f"regime {c} chosen design, evening scenario, case {case}: {key} (select-year mean)",
                    round(float(sm.loc[(c, case), key]), nd), unit, f"g16_serve_r{c}.csv",
                    f"case={case}")

    # --- issue 2: widened-bound diagnostic (scripts/g17_issue2_widen.py)
    for c in REGIMES:
        w = pd.read_csv(OUT / f"g17_widen_r{c}.csv")
        base = json.loads((OUT / f"g10_selection_r{c}.json").read_text(encoding="utf-8"))["chosen"]["explore_g_window"]
        for blk, lv in (("A_radius", "R45"), ("A_radius", "R50"), ("B_fraction", "f0.25"), ("B_fraction", "f0.30"), ("B_fraction", "f0.40"),
                        ("D_flow", "q0.080")):
            v = float(w[(w.block == blk) & (w.level == lv)].g_window.iloc[0]) - float(base)
            add(f"widen.r{c}.{blk}.{lv}", f"regime {c} widened-bound diagnostic: g_window change vs chosen (explore years), {blk} {lv}", round(v, 2),
                "kWh/yr", f"g17_widen_r{c}.csv", f"block={blk}, level={lv}, minus chosen explore g_window")

    # --- issue 1: G9 with and without the box-vertex step (scripts/g18_issue1_compare.py). Not run for Uttarakhand: the vertex
    # step is part of the declared recipe from the start, and the no-vertex comparison needs 12 extra active-learning runs.
    w1 = pd.read_csv(OUT / "g18_issue1_with_without.csv") if (OUT / "g18_issue1_with_without.csv").exists() else         pd.DataFrame(columns=["pair", "state", "eps_g_window", "within_band", "hv_rel_to_best_state"])
    for r in w1[w1.eps_g_window.notna()].itertuples():
        add(f"issue1.{r.pair}.{r.state}.eps_g_window", f"G9 grid check epsilon gap, g_window ({r.pair}, state {r.state})", round(float(r.eps_g_window), 3), "kWh",
            "g18_issue1_with_without.csv", f"pair={r.pair}, state={r.state}")
        add(f"issue1.{r.pair}.{r.state}.within_band", f"G9 grid check within band ({r.pair}, state {r.state})", bool(r.within_band), "",
            "g18_issue1_with_without.csv", f"pair={r.pair}, state={r.state}")
    for r in w1[w1.state != "base"].itertuples():
        add(f"issue1.{r.pair}.{r.state}.hv_rel", f"hypervolume relative to the best state ({r.pair}, state {r.state})", round(float(r.hv_rel_to_best_state), 3),
            "-", "g18_issue1_with_without.csv", f"pair={r.pair}, state={r.state}")

    # --- G9 checks
    gc = pd.read_csv(OUT / "g9_grid_check.csv")
    for r in gc.itertuples():
        for key in ("eps_g_window", "eps_g_annual", "eps_d_overheat", "hv_ratio_final_over_grid"):
            add(f"g9.grid.{r.pair}.{key}", f"G9 dense-grid check {key} ({r.pair})", round(float(getattr(r, key)), 3), "kWh or h or ratio",
                "g9_grid_check.csv", f"pair={r.pair}")
        add(f"g9.grid.{r.pair}.within_band", f"G9 dense-grid check within band ({r.pair})", bool(r.within_band), "", "g9_grid_check.csv",
            f"pair={r.pair}")
    ss = pd.read_csv(OUT / "g9_seed_stability.csv")
    for r in ss.itertuples():
        add(f"g9.seed.{r.pair}.within_band", f"G9 seed spread within band ({r.pair})", bool(r.spread_within_band), "",
            "g9_seed_stability.csv", f"pair={r.pair}")
    al = pd.read_csv(OUT / "g9_al_summary.csv")
    for r in al.itertuples():
        add(f"g9.al.{r.pair}.n_train", f"G9 final training-set size ({r.pair})", int(r.n_train_final), "designs", "g9_al_summary.csv",
            f"pair={r.pair}")
        add(f"g9.al.{r.pair}.rounds", f"G9 active-learning rounds ({r.pair})", int(r.rounds), "rounds", "g9_al_summary.csv", f"pair={r.pair}")

    # --- G11 controls and main effects
    for c in REGIMES:
        d = pd.read_csv(OUT / f"g11_ablation_r{c}.csv")
        f = f"g11_ablation_r{c}.csv"

        def row(block, level):
            return d[(d.block == block) & (d.level == level)].iloc[0]

        add(f"abl.r{c}.base", f"regime {c} ablation base g_window (explore years)", round(float(row("base", "chosen").g_window), 2), "kWh", f, "block=base")
        add(f"abl.r{c}.L0", f"regime {c} latent heat = 0: g_window", round(float(row("pos_control_latent_zero", "L=0").g_window), 2), "kWh", f,
            "block=pos_control_latent_zero")
        add(f"abl.r{c}.Tm45", f"regime {c} synthetic Tm=45 C: g_window", round(float(row("pos_control_Tm45_synthetic", "Tm=45C").g_window), 2),
            "kWh", f, "block=pos_control_Tm45_synthetic")
        add(f"abl.r{c}.N2", f"regime {c} determinism max abs diff", float(row("neg_control_determinism", "rerun").max_abs_diff_vs_base), "", f,
            "block=neg_control_determinism")
        for a in ("bottom", "center", "top"):
            add(f"abl.r{c}.anchor_{a}", f"regime {c} staggered, {a} anchor: g_window",
                round(float(row("arrangement_anchor", f"staggered|{a}").g_window), 2), "kWh", f, f"level=staggered|{a}")
        for lv in d[d.block == "count"].level:
            add(f"abl.r{c}.count_{lv}", f"regime {c} PCM fraction {lv}: g_window", round(float(row("count", lv).g_window), 2), "kWh", f,
                f"block=count, level={lv}")
        for lv in d[d.block == "flow"].level:
            add(f"abl.r{c}.flow_{lv}", f"regime {c} flow {lv}: g_window", round(float(row("flow", lv).g_window), 2), "kWh", f,
                f"block=flow, level={lv}")
        thick = d[d.block == "thickness_const_mass"]
        add(f"abl.r{c}.thickness_valid", f"regime {c} thickness levels with a valid geometry", int(thick.valid.sum()), f"of {len(thick)}", f,
            "block=thickness_const_mass")

    # --- G4 CFD draw case
    g4 = pd.read_csv(OUT / "g4_cfd_draw_case.csv")
    for r in g4.itertuples():
        add(f"g4.cfd.N{r.n_nodes}.{'strat' if 'strat' in r.initial_state else 'mixed'}", "litres at or above 45 C after the draw",
            round(float(r.litres_at_or_above_45C), 1), "L", "g4_cfd_draw_case.csv", f"n_nodes={r.n_nodes}, state={r.initial_state}")

    reg = pd.DataFrame(ROWS)
    reg.to_csv(OUT / "results_registry.csv", index=False, encoding="utf-8")
    print("registry rows", len(reg))


if __name__ == "__main__":
    main()
