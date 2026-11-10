"""
Objective 2 — shared paths and configuration.

Assumes this folder (objective2_design_optimization/) sits as a SIBLING
to the Tamil Nadu Objective 1 pipeline folder:

    project-root/
      era5_tamilnadu/                  <- Objective 1 pipeline (READ-ONLY from here on)
      objective2_design_optimization/  <- this project (everything Obj2 writes lives here)

If your Objective 1 folder has a different name, change OBJ1_ROOT below —
nothing else needs to change.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# ── Objective 1 pipeline (READ-ONLY — Objective 2 must never write here) ──
OBJ1_ROOT = PROJECT_ROOT / "tamilnadu_pipeline"          # <-- edit if your folder name differs
OBJ1_DATA_DIR = OBJ1_ROOT / "data"
OBJ1_PROCESSED_DIR = OBJ1_DATA_DIR / "processed"
OBJ1_PREPROCESSED_DIR = OBJ1_DATA_DIR / "preprocessed"
OBJ1_RAW_POWER_DIR = OBJ1_DATA_DIR / "raw" / "nasapower"

# ── Objective 2's own tree ─────────────────────────────────────────────────
DATA_DIR = BASE_DIR / "data"
OBJ1_FROZEN_DIR = DATA_DIR / "objective1"            # D2.1: frozen copies land here
OBJ1_FROZEN_WEATHER_DIR = OBJ1_FROZEN_DIR / "raw_weather"   # medoid points' hourly cache
PCM_DIR = DATA_DIR / "pcm"
PROCESSED_DIR = DATA_DIR / "processed"               # Obj2's own DOE/surrogate/optimizer output

CONFIGS_DIR = BASE_DIR / "configs"                    # system_config.yaml, design_bounds.yaml
RESULTS_DIR = BASE_DIR / "results"

MANIFEST_FILE = OBJ1_FROZEN_DIR / "manifest.json"


def ensure_dirs():
    for d in (DATA_DIR, OBJ1_FROZEN_DIR, OBJ1_FROZEN_WEATHER_DIR, PCM_DIR,
              PROCESSED_DIR, CONFIGS_DIR, RESULTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
