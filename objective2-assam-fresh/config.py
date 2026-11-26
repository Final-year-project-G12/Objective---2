"""
Objective 2 — shared paths and configuration (Assam).

Assumes this folder (objective2-assam/) sits as a sibling to the
other Objective 2 folders:

    project-root/
      era5-assam/           <- Objective 1 pipeline (READ-ONLY)
      objective2-assam/     <- this project (dedicated Assam Objective 2)

Objective 1's outputs are frozen and copied under data/objective1/,
data/weather/, data/demand/.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# ── Objective 1 pipeline (READ-ONLY — Objective 2 must never write here) ──
def get_obj1_root(state: str = "assam") -> Path:
    candidates = [
        PROJECT_ROOT / f"era5-{state}",
        PROJECT_ROOT.parent / "PCM-Selection-ML-model" / f"era5-{state}",
        PROJECT_ROOT / "PCM-Selection-ML-model" / f"era5-{state}",
        BASE_DIR.parent / "PCM-Selection-ML-model" / f"era5-{state}",
    ]
    for c in candidates:
        if c.exists():
            return c
    return PROJECT_ROOT / f"era5-{state}"

OBJ1_ROOT = get_obj1_root("assam")
OBJ1_DATA_DIR = OBJ1_ROOT / "data"
OBJ1_PROCESSED_DIR = OBJ1_DATA_DIR / "processed"
OBJ1_PREPROCESSED_DIR = OBJ1_DATA_DIR / "preprocessed"
OBJ1_RAW_POWER_DIR = OBJ1_DATA_DIR / "raw" / "nasapower"

# ── Objective 2's own tree ─────────────────────────────────────────────────
DATA_DIR = BASE_DIR / "data"
OBJ1_FROZEN_DIR = DATA_DIR / "objective1"            # D2.1: frozen copies land here
OBJ1_FROZEN_WEATHER_DIR = OBJ1_FROZEN_DIR / "raw_weather"   # medoid points' hourly cache
WEATHER_DIR = DATA_DIR / "weather"                   # per-regime frozen weather profiles
DEMAND_DIR = DATA_DIR / "demand"                     # canonical draw profile
PCM_DIR = DATA_DIR / "pcm"
PROCESSED_DIR = DATA_DIR / "processed"               # Obj2's own DOE/surrogate/optimizer output

CONFIGS_DIR = BASE_DIR / "configs"                    # *_shared.yaml + states/rajasthan.yaml
RESULTS_DIR = BASE_DIR / "results"

MANIFEST_FILE = OBJ1_FROZEN_DIR / "manifest.json"


def ensure_dirs():
    for d in (DATA_DIR, OBJ1_FROZEN_DIR, OBJ1_FROZEN_WEATHER_DIR, WEATHER_DIR,
              DEMAND_DIR, PCM_DIR, PROCESSED_DIR, CONFIGS_DIR, RESULTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
