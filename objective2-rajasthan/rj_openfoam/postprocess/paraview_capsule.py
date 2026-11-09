# pvpython postprocess/paraview_capsule.py <case_dir> [times_s comma-separated]
# Saves melt-front (alpha1) and temperature snapshots of one capsule case, mirrored about the axis,
# to <case_dir>/images/. Run with ParaView's pvpython (5.10+), not plain python.
import os, sys
from paraview.simple import *

case = os.path.abspath(sys.argv[1])
times = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
open(os.path.join(case, "case.foam"), "a").close()
r = OpenFOAMReader(FileName=os.path.join(case, "case.foam"))
r.MeshRegions = ["internalMesh"]
r.CellArrays = ["solidificationMeltingSource1:alpha1", "T", "U"]
ALPHA = "solidificationMeltingSource1:alpha1"   # liquid fraction field written by the ESI fvOption
r.UpdatePipelineInformation()
avail = list(r.TimestepValues) if hasattr(r.TimestepValues, "__len__") else [r.TimestepValues]
times = times or [avail[int(i * (len(avail) - 1) / 4)] for i in range(5)]
cut = Slice(Input=r); cut.SliceType.Normal = [0, 0, 1]
# capsule axis = x, radial = y (see make_capsule_case.py): mirror across y = 0. ParaView 6 renamed Reflect to AxisAlignedReflect.
_Reflect = globals().get("AxisAlignedReflect") or globals().get("Reflect")
mir = _Reflect(Input=cut)
if "PlaneMode" in mir.ListProperties():
    mir.PlaneMode = "Y Min"
else:
    mir.Plane = "Y Min"
os.makedirs(os.path.join(case, "images"), exist_ok=True)
view = GetActiveViewOrCreate("RenderView"); view.ViewSize = [900, 900]; view.OrientationAxesVisibility = 0
for field, rng in ((ALPHA, (0, 1)), ("T", None)):
    d = Show(mir, view); ColorBy(d, ("CELLS", field))
    lut = GetColorTransferFunction(field)
    if rng: lut.RescaleTransferFunction(*rng)
    d.SetScalarBarVisibility(view, True)
    view.CameraPosition = [0, 0, 1]; view.CameraFocalPoint = [0, 0, 0]; view.CameraViewUp = [0, 1, 0]
    view.ResetCamera()
    for t in times:
        view.ViewTime = t
        if field == "T" and rng is None: d.RescaleTransferFunctionToDataRange(False, True)
        SaveScreenshot(os.path.join(case, "images", f"{field.split(chr(58))[-1]}_t{int(t):06d}s.png"), view)
    Hide(mir, view)
# melt front contour (alpha1 = 0.5) as CSV, to compare with Tan 2009 photographs in V0
ctr = Contour(Input=CellDatatoPointData(Input=mir), ContourBy=["POINTS", ALPHA], Isosurfaces=[0.5])
for t in times:
    UpdatePipeline(time=t, proxy=ctr)
    SaveData(os.path.join(case, "images", f"front_t{int(t):06d}s.csv"), proxy=ctr)
print("saved to", os.path.join(case, "images"))
