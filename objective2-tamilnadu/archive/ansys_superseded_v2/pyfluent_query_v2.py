"""
Parameterized results query for the post-demand-timing-fix (2026-10-26)
Fluent cases. Reads back a saved <basename>.cas.h5/.dat.h5 pair and reports
the capsule (PCM, cell zone 3_s_2) liquid fraction and temperature range.

Usage: python pyfluent_query_v2.py <basename>
Example: python pyfluent_query_v2.py regime0_v2_c26_melting
"""
import os
import sys
import ansys.fluent.core as pyfluent

CASE_PATH = os.path.abspath(f"{sys.argv[1]}.cas.h5")
LOCAL_CWD = r"C:\fluent_work"

print("Launching Fluent...")
solver = pyfluent.launch_fluent(
    product_version="26.1.0", dimension=2, precision="double",
    processor_count=2, ui_mode="no_gui_or_graphics", start_timeout=120,
    cwd=LOCAL_CWD,
)
print("Connected.")

solver.file.read_case_data(file_name=CASE_PATH, pdf_file_name="")
print("Case+data loaded.")

solver.solution.report_definitions.volume["capsule_liqfrac"] = {}
rd = solver.solution.report_definitions.volume["capsule_liqfrac"]
rd.report_type = "volume-average"
rd.field = "liquid-fraction"
rd.cell_zones = ["3_s_2"]
val = solver.solution.report_definitions.compute(report_defs=["capsule_liqfrac"])
print("Volume-averaged liquid fraction in capsule:", val)

solver.solution.report_definitions.volume["capsule_tmax"] = {}
rd2 = solver.solution.report_definitions.volume["capsule_tmax"]
rd2.report_type = "volume-max"
rd2.field = "temperature"
rd2.cell_zones = ["3_s_2"]
val2 = solver.solution.report_definitions.compute(report_defs=["capsule_tmax"])
print("Max temperature in capsule (K):", val2)

solver.solution.report_definitions.volume["capsule_tmin"] = {}
rd3 = solver.solution.report_definitions.volume["capsule_tmin"]
rd3.report_type = "volume-min"
rd3.field = "temperature"
rd3.cell_zones = ["3_s_2"]
val3 = solver.solution.report_definitions.compute(report_defs=["capsule_tmin"])
print("Min temperature in capsule (K):", val3)

solver.exit()
print("Clean exit.")
