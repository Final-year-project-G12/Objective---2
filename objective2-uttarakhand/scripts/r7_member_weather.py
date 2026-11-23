"""
scripts/r7_member_weather.py  -  rebuild L7 input: member-point weather for the band's "medoid versus member points" term (plan O2-12)
=======================================================================================================================================
Per regime, the (up to) two NON-medoid member points with the largest population (weather-only, deterministic choice; members from
data/objective1/cluster_assignments_uttarakhand.csv). Their explore-year (2016-2019) files are built from Objective 1's raw NASA POWER
cache with exactly the same cleaning and acceptance rule as the medoids (src/weather/inventory.build_point_year). They are written next
to the medoid files but listed in their own inventory (data/weather/point_years/member_inventory.csv), so the medoid inventory of the
year roles is untouched. Only explore years: the band is computed on the explore years.
Usage: python scripts/r7_member_weather.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.weather import roles                                      # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS, RAW_DIR, build_point_year   # noqa: E402

N_MEMBERS = 2


def members():
    a = pd.read_csv(ROOT / "data" / "objective1" / "cluster_assignments_uttarakhand.csv")
    out = {}
    for cid, med in CURRENT_MEDOIDS.items():
        m = a[(a.cluster_id == cid) & (a.point_id != med)].sort_values("population", ascending=False)
        out[cid] = m.point_id.head(N_MEMBERS).tolist()
    return out


def main():
    rows = []
    for cid, pids in members().items():
        for pid in pids:
            for y in roles.years_for("explore"):
                r, _ = build_point_year(cid, pid, y, raw_dir=RAW_DIR, write=True)
                rows.append(r)
    inv = pd.DataFrame(rows)
    inv.to_csv(roles.WEATHER_POINT_YEARS_DIR / "member_inventory.csv", index=False)
    print(inv.groupby("cluster_id").agg(points=("point_id", "unique"), accepted=("accepted", "sum"), n=("accepted", "size")))


if __name__ == "__main__":
    main()
