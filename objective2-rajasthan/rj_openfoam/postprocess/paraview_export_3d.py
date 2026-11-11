# pvpython postprocess/paraview_export_3d.py <case_dir> <out_dir> [--segments 36] [--every 600] [--span 360]
#
# Turns the 5-degree axisymmetric wedge of one capsule case (axis = x, radial = y; see make_capsule_case.py) into a
# 3-D solid of revolution and writes T, alpha1 (liquid fraction) and U as a time series that ParaView opens directly:
#   <out_dir>/step_<t>.vtm (+ folder with one .vtu) for every chosen time, and <out_dir>/<case>.pvd as the index.
#
# How the solid is built (no ParaView filter does this for volume cells):
#   * every wedge cell is projected to the (x, r) half-plane, r = hypot(y, z); duplicate points are merged, giving one
#     polygon per cell (4 points for the hexahedra, 4 points with 2 on the axis for the prisms that touch the axis);
#   * each polygon is revolved about the x axis through `--span` degrees in `--segments` steps: a quad becomes a
#     hexahedron, a quad with an edge on the axis becomes a wedge (triangular prism);
#   * cell data are copied to every segment. U is rotated per segment: (Ux, Ur, Uz) -> (Ux, Ur cos p - Uz sin p, Ur sin p + Uz cos p)
#     with p the segment's mid-angle, so the vectors point radially all the way round. Ur is the wedge's y component.
# The geometry is built once; only the cell arrays change per time step. The volume of the solid is printed and
# compared with 4/3 pi R^3 (it is slightly smaller: the wedge is a polygonal approximation of the revolution).
# Nothing is interpolated: fields are the solver's cell values, one value per original wedge cell.
import argparse, math, os, shutil, sys
import numpy as np
from paraview.simple import *
from paraview import servermanager as sm
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkMultiBlockDataSet, VTK_HEXAHEDRON, VTK_WEDGE
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkIOXML import vtkXMLMultiBlockDataWriter
from vtkmodules.vtkFiltersVerdict import vtkCellSizeFilter

ALPHA = "solidificationMeltingSource1:alpha1"   # liquid-fraction field written by the ESI fvOption

ap = argparse.ArgumentParser()
ap.add_argument("case_dir")
ap.add_argument("out_dir")
ap.add_argument("--segments", type=int, default=36, help="revolution steps over the span (72 = one per 5-degree wedge)")
ap.add_argument("--every", type=float, default=600.0, help="export every N seconds of simulated time (0 = every written time)")
ap.add_argument("--span", type=float, default=360.0, help="degrees of revolution")
a = ap.parse_args()

case = os.path.abspath(a.case_dir)
name = os.path.basename(case.rstrip("/\\"))
out = os.path.abspath(a.out_dir)
os.makedirs(out, exist_ok=True)
foam = os.path.join(case, "case.foam")
open(foam, "a").close()

rd = OpenFOAMReader(FileName=foam)
rd.MeshRegions = ["internalMesh"]
rd.CellArrays = [ALPHA, "T", "U"]
rd.UpdatePipelineInformation()
all_times = [float(t) for t in (rd.TimestepValues if hasattr(rd.TimestepValues, "__len__") else [rd.TimestepValues])]
times = [t for t in all_times if a.every <= 0 or abs(t / a.every - round(t / a.every)) < 1e-9]
if not times:
    sys.exit("no written time matches --every")
mb = MergeBlocks(Input=rd)


def fetch(t):
    mb.UpdatePipeline(t)
    return sm.Fetch(mb)


# ---- topology from the first time (same cell order at every time)
g0 = fetch(times[0])
nc = g0.GetNumberOfCells()
P = vtk_to_numpy(g0.GetPoints().GetData())
X = P[:, 0]
R = np.hypot(P[:, 1], P[:, 2])
key = {}
xs, rs = [], []


def pid(i):
    k = (round(float(X[i]), 10), round(float(R[i]), 10))
    if k not in key:
        key[k] = len(xs)
        xs.append(k[0]); rs.append(k[1])
    return key[k]


polys = []
for c in range(nc):
    ids = g0.GetCell(c).GetPointIds()
    u = list(dict.fromkeys(pid(ids.GetId(j)) for j in range(ids.GetNumberOfIds())))
    cx = sum(xs[i] for i in u) / len(u); cr = sum(rs[i] for i in u) / len(u)
    u.sort(key=lambda i: math.atan2(rs[i] - cr, xs[i] - cx))          # counter-clockwise in (x, r)
    polys.append(u)
xs = np.array(xs); rs = np.array(rs); m = len(xs)
axis_tol = 1e-9 * max(float(rs.max()), 1e-12)
on_axis = rs < axis_tol

nseg = a.segments
dth = math.radians(a.span) / nseg
full = abs(a.span - 360.0) < 1e-9
nring = nseg if full else nseg + 1
ang = np.arange(nring) * dth
pts = np.empty((nring * m, 3))
for k in range(nring):
    pts[k * m:(k + 1) * m, 0] = xs
    pts[k * m:(k + 1) * m, 1] = rs * np.cos(ang[k])
    pts[k * m:(k + 1) * m, 2] = rs * np.sin(ang[k])


def build(flip):
    """flip: set of cell-type ids whose point order is reversed."""
    grid = vtkUnstructuredGrid()
    vp = vtkPoints(); vp.SetData(numpy_to_vtk(pts.astype(np.float32), deep=True)); grid.SetPoints(vp)
    grid.Allocate(nseg * nc)
    for s in range(nseg):
        r0, r1 = (s % nring) * m, ((s + 1) % nring) * m
        for poly in polys:
            na = [i for i in poly if on_axis[i]]
            if len(poly) == 4 and not na:
                v = [r0 + i for i in poly] + [r1 + i for i in poly]
                t = VTK_HEXAHEDRON
                if t in flip:
                    v = [v[0], v[3], v[2], v[1], v[4], v[7], v[6], v[5]]
            elif len(poly) == 4 and len(na) == 2:
                k = next((j for j in range(4) if on_axis[poly[j]] and on_axis[poly[(j + 1) % 4]]), None)
                if k is None:
                    sys.exit("a cell has two non-adjacent points on the axis")
                a_, b_, c_, d_ = (poly[(k + j) % 4] for j in range(4))        # a, b on the axis; a-b-c-d counter-clockwise
                v = [a_, r0 + d_, r1 + d_, b_, r0 + c_, r1 + c_]              # axis points are the same in every ring
                t = VTK_WEDGE
                if t in flip:
                    v = [v[0], v[2], v[1], v[3], v[5], v[4]]
            else:
                sys.exit(f"unsupported cell shape: {len(poly)} points, {len(na)} on the axis")
            grid.InsertNextCell(t, len(v), v)
    return grid


def sizes(grid):
    f = vtkCellSizeFilter(); f.SetInputData(grid); f.ComputeVolumeOn(); f.ComputeAreaOff(); f.ComputeLengthOff(); f.ComputeVertexCountOff(); f.Update()
    return vtk_to_numpy(f.GetOutput().GetCellData().GetArray("Volume"))


flip = set()
grid = build(flip)
v = sizes(grid)
types = vtk_to_numpy(grid.GetCellTypesArray())
for t in (VTK_HEXAHEDRON, VTK_WEDGE):
    sel = types == t
    if sel.any() and np.median(v[sel]) < 0:
        flip.add(t)
if flip:
    grid = build(flip)
    v = sizes(grid)
bad = int((v <= 0).sum())
Rcap = float(rs.max())
print(f"{name}: {grid.GetNumberOfCells()} cells ({nseg} segments x {nc} wedge cells), {len(times)} time steps, "
      f"min cell volume {v.min():.3e} m3, non-positive cells {bad}, volume {v.sum():.4e} m3 = "
      f"{v.sum() / (4 / 3 * math.pi * Rcap ** 3) * 100:.2f} % of 4/3 pi R^3 (R = {Rcap * 1000:.2f} mm, span {a.span:g} deg)")
if bad:
    sys.exit("cells with non-positive volume: point order is wrong, nothing written")

phi = (np.arange(nseg) + 0.5) * dth
cphi = np.repeat(np.cos(phi), nc); sphi = np.repeat(np.sin(phi), nc)

wr = vtkXMLMultiBlockDataWriter()
pvd = ['<?xml version="1.0"?>', '<VTKFile type="Collection" version="0.1" byte_order="LittleEndian">', "  <Collection>"]
for t in times:
    g = fetch(t)
    cd = g.GetCellData()
    T = vtk_to_numpy(cd.GetArray("T")).copy()
    al = vtk_to_numpy(cd.GetArray(ALPHA)).copy()
    U = vtk_to_numpy(cd.GetArray("U")).copy()
    ux, ur, uz = np.tile(U[:, 0], nseg), np.tile(U[:, 1], nseg), np.tile(U[:, 2], nseg)
    U3 = np.column_stack([ux, ur * cphi - uz * sphi, ur * sphi + uz * cphi])
    for arr, nm in ((np.tile(T, nseg), "T"), (np.tile(al, nseg), "alpha1"), (U3, "U")):
        va = numpy_to_vtk(np.ascontiguousarray(arr, dtype=np.float32), deep=True); va.SetName(nm)
        if nm == "T":
            grid.GetCellData().RemoveArray("T")
        grid.GetCellData().AddArray(va)
    grid.GetCellData().SetActiveScalars("T")
    blk = vtkMultiBlockDataSet(); blk.SetNumberOfBlocks(1); blk.SetBlock(0, grid)
    fn = f"step_{int(round(t)):06d}.vtm"
    wr.SetFileName(os.path.join(out, fn)); wr.SetInputData(blk); wr.SetDataModeToBinary(); wr.SetIdTypeToInt32(); wr.SetCompressorTypeToZLib(); wr.Write()
    pvd.append(f'    <DataSet timestep="{t:g}" group="" part="0" file="{fn}"/>')
    print(f"  t = {t:g} s  T {T.min() - 273.15:.1f}..{T.max() - 273.15:.1f} C  liquid {al.min():.2f}..{al.max():.2f}", flush=True)
pvd += ["  </Collection>", "</VTKFile>"]
with open(os.path.join(out, name + ".pvd"), "w") as f:
    f.write("\n".join(pvd) + "\n")
shutil.copyfile(foam, os.path.join(out, "case.foam"))          # empty marker of the wedge case (opens only where cases/<case> exists)
print("wrote", os.path.join(out, name + ".pvd"))
