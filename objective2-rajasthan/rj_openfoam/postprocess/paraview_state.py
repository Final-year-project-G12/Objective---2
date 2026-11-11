# pvpython postprocess/paraview_state.py <case.pvd> <out.pvsm> [preview.png]
# Builds one ParaView state on the exported 3-D series (paraview_export_3d.py) and saves it:
#   * mid-plane slice (z = 0) coloured by temperature (colour range = the case's own T range over the whole series),
#   * molten front = iso-surface of the liquid fraction alpha1 = 0.5, clipped to z >= 0 and drawn semi-transparent,
#   * outline of the sphere, temperature colour bar, time shown in the title.
# Open the .pvsm with File > Load State and choose "Search files under specified directory" if ParaView asks for the .pvd.
import os, sys
from paraview.simple import *

pvd = os.path.abspath(sys.argv[1])
state = os.path.abspath(sys.argv[2])
png = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else None
title = os.path.splitext(os.path.basename(pvd))[0]

src = PVDReader(registrationName=title, FileName=pvd)
src.UpdatePipelineInformation()
times = list(src.TimestepValues) if hasattr(src.TimestepValues, "__len__") else [src.TimestepValues]
scene = GetAnimationScene(); scene.UpdateAnimationUsingDataTimeSteps()
view = GetActiveViewOrCreate("RenderView"); view.ViewSize = [1100, 900]; view.OrientationAxesVisibility = 1
view.Background = [1, 1, 1]
try:
    view.UseColorPaletteForBackground = 0
except Exception:
    pass

lo, hi = 1e30, -1e30
for t_ in times:                                   # colour range over the whole series, so frames are comparable
    src.UpdatePipeline(t_)
    a_, b_ = src.CellData["T"].GetRange(); lo, hi = min(lo, a_), max(hi, b_)
Tr = (lo, hi)
sl = Slice(registrationName="mid-plane z=0", Input=src); sl.SliceType = "Plane"
sl.SliceType.Origin = [0, 0, 0]; sl.SliceType.Normal = [0, 0, 1]
dsl = Show(sl, view); ColorBy(dsl, ("CELLS", "T"))
lutT = GetColorTransferFunction("T"); lutT.ApplyPreset("Inferno", True)
lutT.RescaleTransferFunction(Tr[0], Tr[1]); lutT.AutomaticRescaleRangeMode = "Never"      # keep the series range when a frame is nearly uniform
dsl.SetScalarBarVisibility(view, True)
bar = GetScalarBar(lutT, view); bar.Title = "T [K]"; bar.TitleColor = [0, 0, 0]; bar.LabelColor = [0, 0, 0]

c2p = CellDatatoPointData(registrationName="cell to point", Input=src)
ct = Contour(registrationName="melt front alpha1=0.5", Input=c2p); ct.ContourBy = ["POINTS", "alpha1"]; ct.Isosurfaces = [0.5]
ct.ComputeNormals = 1
cl = Clip(registrationName="front z>=0", Input=ct); cl.ClipType = "Plane"
cl.ClipType.Origin = [0, 0, 0]; cl.ClipType.Normal = [0, 0, 1]
try:
    cl.Invert = 0
except Exception:
    pass
dcl = Show(cl, view); ColorBy(dcl, None); dcl.AmbientColor = dcl.DiffuseColor = [0.15, 0.45, 0.85]; dcl.Opacity = 0.35

ol = Outline(registrationName="outline", Input=src)
dol = Show(ol, view); dol.AmbientColor = dol.DiffuseColor = [0.2, 0.2, 0.2]

tt = AnnotateTimeFilter(registrationName="time", Input=src); tt.Format = title + "   t = {time:.0f} s"
dtt = Show(tt, view); dtt.WindowLocation = "Upper Center"; dtt.Color = [0, 0, 0]

# gravity points along -x in these cases, so the capsule is shown with x up
view.CameraPosition = [0.0, 0.0, 0.2]; view.CameraFocalPoint = [0, 0, 0]; view.CameraViewUp = [1, 0, 0]
view.ResetCamera()
Render(view)
if png:
    scene.AnimationTime = times[min(1, len(times) - 1)]      # an early frame (second exported time), where the melt front is still inside
    SaveScreenshot(png, view, ImageResolution=[1100, 900])
scene.AnimationTime = times[0]
SaveState(state)
print("saved", state)
