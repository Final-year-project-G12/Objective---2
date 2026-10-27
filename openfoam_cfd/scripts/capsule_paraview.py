# capsule_paraview.py -- ParaView script for a --viz capsule case (wedge, axisymmetric)
#
# Headless snapshots (no window):
#   "D:\Program Files\ParaView 6.2.0\bin\pvbatch.exe" capsule_paraview.py <case.foam> [outdir]
# GUI with the pipeline already built (set the case path first):
#   $env:CAPSULE_FOAM="<case.foam>"; & "D:\Program Files\ParaView 6.2.0in\paraview.exe" --script="<this file>"
#   or: Tools -> Python Shell -> Run Script (with CAPSULE_FOAM set in the environment).
#
# Pipeline: OpenFOAM reader -> Reflect (mirror across the axis: y -> -y) -> colour by liquid fraction.
import os
import sys

from paraview.simple import *  # noqa: F401,F403

headless = (sys.argv[0].lower().endswith("pvbatch.exe") or "pvbatch" in sys.argv[0].lower())
case = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CAPSULE_FOAM")
outdir = sys.argv[2] if len(sys.argv) > 2 else (os.path.dirname(case) if case else ".")
if case is None:
    raise SystemExit("usage: capsule_paraview.py <case.foam> [outdir]")

reader = OpenFOAMReader(registrationName="capsule", FileName=case)
reader.MeshRegions = ["internalMesh"]
reader.UpdatePipelineInformation()
reader.CellArrays = [a for a in reader.CellArrays.Available]
times = list(reader.TimestepValues)
print("time steps:", len(times), "first/last:", times[0], times[-1])
print("cell arrays:", list(reader.CellArrays.Available))

# the field name contains ':' (alpha1 of the solidificationMeltingSource); on Windows it may carry a
# private-use character instead, so match by suffix
alpha = next((n for n in reader.CellArrays.Available if n.endswith("alpha1")), None)
print("liquid-fraction array:", repr(alpha))

# ParaView 6 renamed the Reflect filter to AxisAlignedReflect; older versions use Reflect
_Reflect = globals().get("AxisAlignedReflect") or globals().get("Reflect")
src = reader
if alpha:
    # the reader LISTS the array with a private-use character where the data actually carries ':'
    alpha = alpha.replace("", ":")
mirror = _Reflect(Input=src)
print("reflect properties:", mirror.ListProperties())
_props = mirror.ListProperties()
if "PlaneMode" in _props:
    mirror.PlaneMode = "Y Min"          # ParaView >= 6
else:
    mirror.Plane = "Y Min"              # ParaView 5.x
if "CopyInput" in mirror.ListProperties():
    mirror.CopyInput = 1

view = GetActiveViewOrCreate("RenderView")
view.OrientationAxesVisibility = 0
view.CameraPosition = [0, 0, 1]
view.CameraFocalPoint = [0, 0, 0]
view.CameraViewUp = [1, 0, 0]          # capsule axis (x) vertical, "up" = +x
if hasattr(view, "UseColorPaletteForBackground"):
    view.UseColorPaletteForBackground = 0
view.Background = [1, 1, 1]
disp = Show(mirror, view)
disp.Representation = "Surface"


_used = []


def color_by(name, lo, hi, cmap):
    for _l in _used:                       # hide the previous colour bar
        GetScalarBar(_l, view).Visibility = 0
    ColorBy(disp, ("CELLS", name))
    lut = GetColorTransferFunction(name)
    for _name in (cmap, "Inferno (matplotlib)", "Black-Body Radiation"):
        try:
            if lut.ApplyPreset(_name, True):
                break
        except RuntimeError:
            continue
    lut.RescaleTransferFunction(lo, hi)
    disp.SetScalarBarVisibility(view, True)
    _used.append(lut)
    bar = GetScalarBar(lut, view)
    bar.Visibility = 1
    bar.TitleColor = [0, 0, 0]
    bar.LabelColor = [0, 0, 0]
    return lut


if alpha:
    color_by(alpha, 0.0, 1.0, "Cool to Warm")
view.ResetCamera()
view.CameraParallelProjection = 1

if "pvbatch" in os.path.basename(sys.executable).lower() or headless:
    os.makedirs(outdir, exist_ok=True)
    picks = [t for t in (0, 300, 600, 900, 1200, 1800, 2400) if t <= times[-1]]
    for t in picks:
        tt = min(times, key=lambda x: abs(x - t))
        view.ViewTime = tt
        Render(view)
        fn = os.path.join(outdir, "paraview_liquid_fraction_%05d.png" % int(tt))
        SaveScreenshot(fn, view, ImageResolution=[700, 700])
        print("wrote", fn)
    if "T" in reader.CellArrays.Available:
        color_by("T", 300, 335, "Inferno (matplotlib)")
        for t in (picks[len(picks) // 2], picks[-1]):
            tt = min(times, key=lambda x: abs(x - t))
            view.ViewTime = tt
            Render(view)
            fn = os.path.join(outdir, "paraview_T_%05d.png" % int(tt))
            SaveScreenshot(fn, view, ImageResolution=[700, 700])
            print("wrote", fn)
else:
    Render(view)
    print("pipeline ready: use the time slider / Play; change colouring in the Properties panel")
