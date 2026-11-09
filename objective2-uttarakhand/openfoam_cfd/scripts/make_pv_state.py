# make_pv_state.py -- build a ready-to-play ParaView state file (.pvsm) for a tank or collector case.
#   pvbatch.exe make_pv_state.py tank <case.foam> <out.pvsm> [scalar-range-lo hi]
# Open the result with ParaView:  File -> Load State -> pick the .pvsm  (choose "Use File Paths from State").
# The time slider is set to the full range; press the green Play button.
import sys

from paraview.simple import *  # noqa: F401,F403

kind, case, out = sys.argv[1], sys.argv[2], sys.argv[3]
lo = float(sys.argv[4]) if len(sys.argv) > 4 else None
hi = float(sys.argv[5]) if len(sys.argv) > 5 else None

reader = OpenFOAMReader(registrationName="case", FileName=case)
reader.UpdatePipelineInformation()
regs = list(reader.GetProperty("MeshRegions").Available)
reader.MeshRegions = ([r for r in regs if r.startswith("/") and r.endswith("internalMesh")]
                      if kind == "collector" else ["internalMesh"])
reader.UpdatePipelineInformation()
reader.CellArrays = list(reader.CellArrays.Available)
reader.SkipZeroTime = 0
times = list(reader.TimestepValues)
view = GetActiveViewOrCreate("RenderView")
if hasattr(view, "UseColorPaletteForBackground"):
    view.UseColorPaletteForBackground = 0
view.Background = [1, 1, 1]
view.OrientationAxesVisibility = 0

if kind == "tank":
    refl = globals().get("AxisAlignedReflect") or globals().get("Reflect")
    src = refl(Input=reader)
    if "PlaneMode" in src.ListProperties():
        src.PlaneMode = "Y Min"
    else:
        src.Plane = "Y Min"
    if "CopyInput" in src.ListProperties():
        src.CopyInput = 1
    view.CameraPosition, view.CameraFocalPoint, view.CameraViewUp = [0, 0, 1], [0, 0, 0], [1, 0, 0]
else:
    merged = MergeBlocks(Input=reader)
    src = Transform(Input=merged)
    src.Transform.Scale = [1.0, 12.0, 12.0]
    view.CameraPosition, view.CameraFocalPoint, view.CameraViewUp = [0.6, -1.6, 0.35], [0.6, 0.35, -0.05], [0, 0, 1]

disp = Show(src, view)
disp.Representation = "Surface"
disp.Ambient, disp.Diffuse = 1.0, 0.0
ColorBy(disp, ("CELLS", "T"))
lut = GetColorTransferFunction("T")
for p in ("Inferno (matplotlib)", "Black-Body Radiation", "Cool to Warm"):
    try:
        if lut.ApplyPreset(p, True):
            break
    except RuntimeError:
        continue
if lo is not None:
    lut.RescaleTransferFunction(lo, hi)
    lut.AutomaticRescaleRangeMode = "Never"
else:
    lut.AutomaticRescaleRangeMode = "Update on Apply"
bar = GetScalarBar(lut, view)
bar.Title = "T [K]"
bar.ComponentTitle = ""
bar.TitleColor = bar.LabelColor = [0, 0, 0]
bar.Visibility = 1
disp.SetScalarBarVisibility(view, True)
view.ResetCamera()
anim = GetAnimationScene()
anim.UpdateAnimationUsingDataTimeSteps()
if times:
    anim.AnimationTime = times[0]
SaveState(out)
print("saved", out, "| time steps:", len(times))
