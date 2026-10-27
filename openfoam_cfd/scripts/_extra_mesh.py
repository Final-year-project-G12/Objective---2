import copy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_doe as rd, make_case as mc
cfg = mc.load_cfg()
ref = dict(pcm="RT44HC", d=0.06, mdot=0.03, dT=15.0)
jobs = [dict(id="mesh_006", tag="mesh", cell=0.0006, **ref)]
cfg2 = copy.deepcopy(cfg); cfg2["numerics"]["max_co"] = 0.25
rows = rd.execute(jobs, cfg, os.path.join(rd.ROOT, "cases", "mesh"), 1, False, 6.0)
jobs2 = [dict(id="dt_co025", tag="dt", cell=0.0012, **ref)]
rows += rd.execute(jobs2, cfg2, os.path.join(rd.ROOT, "cases", "mesh"), 1, False, 6.0)
rd.write_csv(rows, os.path.join(rd.ROOT, "results", "cfd_mesh_extra_results.csv"))
