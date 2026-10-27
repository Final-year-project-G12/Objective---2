# capsule_movie.py -- render a --viz capsule case as an animation (frames + GIF).
#
#   "D:\Program Files\ParaView 6.2.0\bin\pvbatch.exe" capsule_movie.py <case.foam> [outdir] [field]
#     field = liquid (default) | T | U
#
# Output: <outdir>\frames\*.png  and  <outdir>\<name>_<field>.gif   (GIF needs Pillow; PNG frames always)
import glob
import os
import sys

from paraview.simple import *  # noqa: F401,F403

case = sys.argv[1]
outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(case), "movie")
field = sys.argv[3] if len(sys.argv) > 3 else "liquid"
name = os.path.splitext(os.path.basename(case))[0]
frames_dir = os.path.join(outdir, "frames_" + field)
os.makedirs(frames_dir, exist_ok=True)
for f in glob.glob(os.path.join(frames_dir, "*.png")):
    os.remove(f)

reader = OpenFOAMReader(registrationName="capsule", FileName=case)
reader.MeshRegions = ["internalMesh"]
reader.UpdatePipelineInformation()
reader.CellArrays = list(reader.CellArrays.Available)
times = list(reader.TimestepValues)
alpha = next(n for n in reader.CellArrays.Available if n.endswith("alpha1")).replace("\uf03a", ":")

_Reflect = globals().get("AxisAlignedReflect") or globals().get("Reflect")
mirror = _Reflect(Input=reader)
if "PlaneMode" in mirror.ListProperties():
    mirror.PlaneMode = "Y Min"
else:
    mirror.Plane = "Y Min"
if "CopyInput" in mirror.ListProperties():
    mirror.CopyInput = 1

view = GetActiveViewOrCreate("RenderView")
view.OrientationAxesVisibility = 0
if hasattr(view, "UseColorPaletteForBackground"):
    view.UseColorPaletteForBackground = 0
view.Background = [1, 1, 1]
view.CameraPosition = [0, 0, 1]
view.CameraFocalPoint = [0, 0, 0]
view.CameraViewUp = [1, 0, 0]
disp = Show(mirror, view)
disp.Representation = "Surface"

if field == "T":
    arr, lo, hi, presets, label = "T", 300.0, 335.0, ("Inferno (matplotlib)", "Black-Body Radiation"), "T [K]"
elif field == "U":
    ColorBy(disp, ("CELLS", "U", "Magnitude"))
    arr, lo, hi, presets, label = "U", 0.0, 0.004, ("Viridis (matplotlib)", "Cool to Warm"), "|U| [m/s]"
else:
    arr, lo, hi, presets, label = alpha, 0.0, 1.0, ("Cool to Warm",), "liquid fraction"
if field != "U":
    ColorBy(disp, ("CELLS", arr))
lut = GetColorTransferFunction(arr)
for p in presets:
    try:
        if lut.ApplyPreset(p, True):
            break
    except RuntimeError:
        continue
lut.RescaleTransferFunction(lo, hi)
bar = GetScalarBar(lut, view)
bar.Visibility = 1
bar.Title = label
bar.ComponentTitle = ""
bar.TitleColor = [0, 0, 0]
bar.LabelColor = [0, 0, 0]
disp.SetScalarBarVisibility(view, True)

txt = Text(Text="t = 0 min")
tdisp = Show(txt, view)
tdisp.Color = [0, 0, 0]
tdisp.FontSize = 28
tdisp.WindowLocation = "Upper Left Corner"

view.ResetCamera()
view.CameraParallelProjection = 1
step = max(1, len(times) // 120)            # <= ~120 frames
for i, t in enumerate(times[::step]):
    view.ViewTime = t
    txt.Text = "t = %.1f min" % (t / 60.0)
    Render(view)
    SaveScreenshot(os.path.join(frames_dir, "f%04d.png" % i), view, ImageResolution=[640, 640])
print("frames:", len(glob.glob(os.path.join(frames_dir, "*.png"))), "in", frames_dir)

try:
    from PIL import Image
    files = sorted(glob.glob(os.path.join(frames_dir, "*.png")))
    imgs = [Image.open(f).convert("P", palette=Image.ADAPTIVE) for f in files]
    gif = os.path.join(outdir, "%s_%s.gif" % (name, field))
    imgs[0].save(gif, save_all=True, append_images=imgs[1:], duration=80, loop=0, optimize=True)
    print("wrote", gif)
except Exception as ex:                      # Pillow missing in ParaView's Python
    print("GIF not written (%r); use scripts\\frames_to_gif.py with system Python" % ex)
