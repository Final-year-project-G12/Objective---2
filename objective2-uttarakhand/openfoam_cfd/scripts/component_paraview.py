# component_paraview.py -- ParaView views for the tank and collector cases
#
# Headless PNGs:
#   pvbatch.exe component_paraview.py tank      <case.foam> [outdir]
#   pvbatch.exe component_paraview.py collector <case.foam> [outdir]
# GUI with the pipeline already built:
#   set CASE_KIND=tank|collector and CASE_FOAM=<case.foam>, then
#   paraview.exe --script=component_paraview.py
#
# tank      : axisymmetric wedge -> mirrored full cross-section, coloured by T at several times
# collector : two regions (water, copper) of one riser strip, coloured by T, 3-D view
import os
import sys

from paraview.simple import *  # noqa: F401,F403

argv = [a for a in sys.argv[1:] if not a.startswith("--")]
kind = argv[0] if argv else os.environ.get("CASE_KIND", "tank")
case = argv[1] if len(argv) > 1 else os.environ.get("CASE_FOAM")
outdir = argv[2] if len(argv) > 2 else (os.path.join(os.path.dirname(case), "paraview") if case else ".")
if not case:
    raise SystemExit("usage: component_paraview.py tank|collector <case.foam> [outdir]")
headless = "pvbatch" in os.path.basename(sys.executable).lower()
os.makedirs(outdir, exist_ok=True)

reader = OpenFOAMReader(registrationName=os.path.basename(case), FileName=case)
reader.UpdatePipelineInformation()
regions = list(reader.GetProperty("MeshRegions").Available) if hasattr(reader.GetProperty("MeshRegions"), "Available") else []
print("mesh regions available:", regions)
if kind == "collector":
    want = [r for r in regions if r.startswith("/") and r.endswith("internalMesh")]   # /water/..., /copper/...
    reader.MeshRegions = want or regions
else:
    reader.MeshRegions = ["internalMesh"]
reader.UpdatePipelineInformation()
reader.CellArrays = list(reader.CellArrays.Available)
times = list(reader.TimestepValues)
print("time steps:", len(times), "first/last:", times[0] if times else None, times[-1] if times else None)

view = GetActiveViewOrCreate("RenderView")
view.OrientationAxesVisibility = 1 if kind == "collector" else 0
if hasattr(view, "UseColorPaletteForBackground"):
    view.UseColorPaletteForBackground = 0
view.Background = [1, 1, 1]

src = reader
if kind == "tank":
    refl = globals().get("AxisAlignedReflect") or globals().get("Reflect")
    src = refl(Input=reader)
    if "PlaneMode" in src.ListProperties():
        src.PlaneMode = "Y Min"
    else:
        src.Plane = "Y Min"
    if "CopyInput" in src.ListProperties():
        src.CopyInput = 1
    view.CameraPosition = [0, 0, 1]
    view.CameraFocalPoint = [0, 0, 0]
    view.CameraViewUp = [1, 0, 0]
    view.CameraParallelProjection = 1
else:
    merged = MergeBlocks(Input=reader)
    src = merged            # whole strip; slices are taken below

def style(disp, view):
    disp.Representation = "Surface"
    disp.Ambient = 1.0          # flat colours: no lighting wash-out
    disp.Diffuse = 0.0
    ColorBy(disp, ("CELLS", "T"))
    lut = GetColorTransferFunction("T")
    for p in ("Inferno (matplotlib)", "Black-Body Radiation", "Cool to Warm"):
        try:
            if lut.ApplyPreset(p, True):
                break
        except RuntimeError:
            continue
    bar = GetScalarBar(lut, view)
    bar.Title = "T [K]"
    bar.ComponentTitle = ""
    bar.TitleColor = [0, 0, 0]
    bar.LabelColor = [0, 0, 0]
    bar.Visibility = 1
    disp.SetScalarBarVisibility(view, True)
    return lut


def snap(fn, size):
    Render(view)
    SaveScreenshot(fn, view, ImageResolution=size)
    print("wrote", fn)


txt = Text(Text="")
tdisp = Show(txt, view)
tdisp.Color = [0, 0, 0]
tdisp.FontSize = 11
tdisp.WindowLocation = "Upper Left Corner"

if headless:
    picks = sorted(set(times[int(round(i * (len(times) - 1) / 5))] for i in range(6))) if times else [0.0]
    if kind == "tank":
        disp = Show(src, view)
        lut = style(disp, view)
        view.ResetCamera()
        for t in picks:
            view.ViewTime = t
            src.UpdatePipeline(t)
            rng = src.CellData["T"].GetRange()
            lut.RescaleTransferFunction(rng[0], rng[1])
            txt.Text = "tank   t = %.1f min   (T %.0f-%.0f K)" % (t / 60.0, rng[0], rng[1])
            snap(os.path.join(outdir, "tank_T_%06d.png" % int(t)), [600, 900])
    else:
        t = times[-1]
        view.ViewTime = t
        merged.UpdatePipeline(t)
        # cross-sections (y-z) at three stations along the riser, looking down the flow direction
        view.CameraParallelProjection = 1
        view.OrientationAxesVisibility = 1
        for xs in (0.05, 0.6, 1.19):
            sl = Slice(Input=merged)
            sl.SliceType = "Plane"
            sl.SliceType.Origin = [xs, 0, 0]
            sl.SliceType.Normal = [1, 0, 0]
            sl.UpdatePipeline(t)
            d = Show(sl, view)
            lut = style(d, view)
            rng = sl.CellData["T"].GetRange()
            lut.RescaleTransferFunction(rng[0], rng[1])
            view.CameraPosition = [xs + 1.0, 0.03, -0.004]
            view.CameraFocalPoint = [xs, 0.03, -0.004]
            view.CameraViewUp = [0, 0, 1]
            view.ResetCamera()
            txt.Text = "collector cross-section at x = %.2f m (flow toward the viewer)   T %.1f-%.1f K" % (xs, rng[0], rng[1])
            snap(os.path.join(outdir, "collector_section_x%03d.png" % int(xs * 100)), [1000, 400])
            Hide(sl, view)
        # longitudinal slice through the middle of the channel (y = 2 mm), z stretched 12x
        sl = Slice(Input=merged)
        sl.SliceType = "Plane"
        sl.SliceType.Origin = [0, 0.002, 0]
        sl.SliceType.Normal = [0, 1, 0]
        tr = Transform(Input=sl)
        tr.Transform.Scale = [1.0, 1.0, 12.0]
        tr.UpdatePipeline(t)
        d = Show(tr, view)
        lut = style(d, view)
        rng = tr.CellData["T"].GetRange()
        lut.RescaleTransferFunction(rng[0], rng[1])
        view.CameraPosition = [0.6, -1.5, -0.04]
        view.CameraFocalPoint = [0.6, 0.0, -0.04]
        view.CameraViewUp = [0, 0, 1]
        view.ResetCamera()
        txt.Text = "collector, longitudinal section y = 2 mm (z x12): water below, plate on top, flow to the right   T %.1f-%.1f K" % rng
        snap(os.path.join(outdir, "collector_longitudinal.png"), [1400, 500])
else:
    disp = Show(src, view)
    style(disp, view)
    view.ResetCamera()
    Render(view)
    print("pipeline ready; use the time slider; add Filters -> Slice for sections")
