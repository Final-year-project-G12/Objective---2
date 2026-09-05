"""
config.py — shared paths for the Objective 2 input-package build scripts (Rajasthan).

Rajasthan counterpart of the Tamil Nadu teammate's config.py. Only the constants in
the "EDIT FOR YOUR STATE" block below change per state; every downstream script reads
paths from here so no filename is hard-coded twice.

Layout note — this repo differs from the Tamil Nadu project on purpose:
  Tamil Nadu:  data/objective1/  data/weather/  data/demand/     (one state per repo)
  here:        data/objective1/<state>/{...,weather/,demand/,raw_weather/}
Objective 2 is being assembled for four states in ONE repo, so weather/ and demand/
live inside the state folder instead of beside it. Relative structure is otherwise
identical, so the shared src/design, src/simulation and src/surrogate code only needs
STATE_DIR handed to it.
"""

from pathlib import Path

# ── EDIT FOR YOUR STATE ──────────────────────────────────────────────────────
STATE = "rajasthan"
OBJ1_FOLDER_NAME = "era5-rajasthan"      # folder under PCM-Selection-ML-model/
POINT_ID_PREFIX = "RJP_"                 # RJP_0001 … RJP_0320

# ── Objective 1 source tree (read-only — never written to by these scripts) ──
REPO_ROOT = Path(__file__).resolve().parent          # .../OBJECTIVE2/Objective---2
PROJECT_ROOT = REPO_ROOT.parents[1]                  # .../Final Year Project
OBJ1_ROOT = PROJECT_ROOT / "PCM-Selection-ML-model" / OBJ1_FOLDER_NAME

OBJ1_PROCESSED_DIR = OBJ1_ROOT / "data" / "processed"
OBJ1_PREPROCESSED_DIR = OBJ1_ROOT / "data" / "preprocessed"
OBJ1_RAW_POWER_DIR = OBJ1_ROOT / "data" / "raw" / "nasapower"
OBJ1_OUTPUTS_DIR = OBJ1_ROOT / "outputs"

# Shared PCM property database — the exact file 07_feasibility_filter_rajasthan.py
# and 08_mcdm_ranking_rajasthan.py read (both resolve it as BASE_DIR.parent/PCM_data/…).
PCM_PROPERTIES_CSV = (OBJ1_ROOT.parent / "PCM_data" / "data"
                      / "PCM_Properties_cleaned_mice_pmm_detailed.csv")

# ── Objective 2 destination tree ─────────────────────────────────────────────
DATA_DIR = REPO_ROOT / "data"
STATE_DIR = DATA_DIR / "objective1" / STATE
FROZEN_DIR = STATE_DIR                        # frozen O1 tables sit at the state root
FROZEN_WEATHER_DIR = STATE_DIR / "raw_weather"   # medoids' raw NASA POWER JSON
WEATHER_DIR = STATE_DIR / "weather"              # per-regime representative weather
DEMAND_DIR = STATE_DIR / "demand"                # canonical draw profile
MANIFEST_FILE = STATE_DIR / "manifest.json"

ALL_DIRS = [DATA_DIR, STATE_DIR, FROZEN_WEATHER_DIR, WEATHER_DIR, DEMAND_DIR]


def ensure_dirs():
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


def obj1_available() -> bool:
    return OBJ1_ROOT.exists()
