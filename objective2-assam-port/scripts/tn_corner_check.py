"""Can Objective 1's SHORTLISTED PCMs beat the water-only tank in every
regime once the design levers are stacked, rather than swept one at a time?

The lever sweep moved R_in, fraction and flow independently around a mid
reference. The optimiser will combine them, so the question that matters
is what the best COMBINATION reaches -- in particular for regime 1, the
only regime where no shortlisted PCM was clearly ahead at mid design."""
import os, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from config import STATE

def _one(job):
    cid, pcm, r, f, q, a = job
    from src.optimize.evaluate import evaluate_design
    try:
        res = evaluate_design(cid, pcm, r, f, q, a, purpose="explore", years=[2016])
        py = (res.get("per_year") or [{}])[0]
        return dict(regime=cid, pcm=pcm, R_in_m=r, fraction=f, flow=q, arr=a,
                    N=res.get("N"), valid=res.get("valid"), reason=res.get("reason",""),
                    g_window=py.get("g_window"), g_annual=py.get("g_annual"),
                    t_pcm_max=py.get("t_pcm_max"), d_overheat=py.get("d_overheat"))
    except Exception as e:
        return dict(regime=cid, pcm=pcm, R_in_m=r, fraction=f, flow=q, arr=a,
                    valid=False, reason=f"{type(e).__name__}: {e}"[:100])

if __name__ == "__main__":
    for v in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS"): os.environ.setdefault(v,"1")
    from src.io_utils import get_regime
    jobs=[]
    for cid in (0,1,2):
        for pcm in get_regime(STATE,cid)["pcm_shortlist"]:
            for r in (0.034, 0.040):
                for f in (0.20, 0.25, 0.30):
                    for a in ("staggered","single-layer","radial"):
                        jobs.append((cid,pcm,r,f,0.020,a))
    print(f"{len(jobs)} combined-lever evaluations", flush=True)
    t0=time.time(); rows=[]
    with ProcessPoolExecutor(max_workers=int(sys.argv[1]) if len(sys.argv)>1 else 6) as ex:
        for i,row in enumerate(ex.map(_one, jobs),1):
            rows.append(row)
            if i%30==0: print(f"  {i}/{len(jobs)} {(time.time()-t0)/60:.1f} min", flush=True)
    import pandas as pd
    df=pd.DataFrame(rows); df.to_csv(ROOT/"results"/"tn_corner_check.csv", index=False)
    ok=df[df.valid==True]
    pd.set_option("display.width",200)
    print("\nBEST shortlisted design per regime (combined levers):")
    print(ok.loc[ok.groupby("regime")["g_window"].idxmax()][
        ["regime","pcm","R_in_m","fraction","flow","arr","N","g_window","g_annual","t_pcm_max","d_overheat"]].round(3).to_string(index=False))
    print("\nbest per (regime, pcm):")
    print(ok.loc[ok.groupby(["regime","pcm"])["g_window"].idxmax()][
        ["regime","pcm","R_in_m","fraction","arr","g_window","t_pcm_max"]].round(2).to_string(index=False))
    print(f"\n{(time.time()-t0)/60:.1f} min")
