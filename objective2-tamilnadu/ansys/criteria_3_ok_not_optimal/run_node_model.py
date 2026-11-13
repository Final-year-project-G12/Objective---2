"""Node-model side of THIS criteria (3. NOT optimal, but working): objective values, gates, funnel verdict, one-day time behaviour.
Run from the project root: python ansys/criteria_3_ok_not_optimal/run_node_model.py
(re-simulates the optimum too, because every number is reported against it)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "criteria_common"))
import run_node_model
run_node_model.main(only="criteria_3_ok_not_optimal")
