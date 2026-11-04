"""Import the refined CGNS mesh and save it as a Fluent mesh-only case.

'cgns-mesh' is the allowed file_type (probe_ftypes.py read the enum off the
solver). An earlier attempt passed invalid types first and Fluent dropped the
connection on the third call, so this uses a fresh session and the valid type
only -- a rejected value can leave the session unusable.
"""
import os, shutil
import ansys.fluent.core as pyfluent

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = r"C:\fluent_work"
shutil.copy(os.path.join(HERE, "regime0_v3_capsule.cgns"),
            os.path.join(WORK, "regime0_v3_capsule.cgns"))

s = pyfluent.launch_fluent(product_version="26.1.0", dimension=2, precision="double",
                           processor_count=2, ui_mode="no_gui_or_graphics",
                           start_timeout=120, cwd=WORK)
s.file.import_.read(file_type="cgns-mesh", file_name="regime0_v3_capsule.cgns")
print("imported OK")
out = os.path.join(WORK, "regime0_v3_REIMPORT_test.cas.h5")
s.file.write_case(file_name=out)
print("wrote", out)
s.exit()
