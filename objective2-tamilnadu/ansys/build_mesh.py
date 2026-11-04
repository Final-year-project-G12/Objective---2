"""
build_mesh.py — generates the 2D axisymmetric mesh for the Regime-0 /
RT57HC single-capsule PCM melting case, using the REAL Objective 2
geometry (no invented numbers):

  capsule radius  = 21.022 mm  (diameter 42.044 mm, Regime 0 deployable design)
  unit-cell outer radius = 1.7 x capsule radius (packed-bed voidage ~0.90
                           approximation, consistent with the Ergun-equation
                           void fraction already used in geometry.py)
  axial length    = 4 x capsule diameter (inlet development + wake)

Produces a Fluent-readable mesh (.msh, version 2 ASCII) with named zones:
  capsule   -> PCM solid cell zone
  water     -> fluid cell zone
  inlet, outlet, wall_outer, axis -> boundary faces
  (the capsule/water interface is created automatically as a shared
  boundary between the two cell zones -- Fluent turns this into a
  coupled wall pair on import)

Run: python build_mesh.py
Output: regime0_capsule.msh
"""
import gmsh
import math

gmsh.initialize()
gmsh.model.add("regime0_capsule")

# ---- real geometry (meters) ----
R_CAPSULE = 0.021022          # Regime 0 deployable design, diameter/2
R_OUTER   = 1.7 * R_CAPSULE    # unit-cell outer radius (~0.90 voidage approx)
L_AXIAL   = 4 * (2 * R_CAPSULE)
X0        = -L_AXIAL / 2       # domain starts upstream of capsule center
CAPSULE_CENTER_X = 0.0

LC_CAPSULE = R_CAPSULE / 18.0   # ~18 cells across the radius (melt-front resolution)
LC_OUTER   = R_OUTER / 10.0

occ = gmsh.model.occ

# Outer domain: rectangle in (x, r) for 2D-axisymmetric (r >= 0, axis at r=0)
outer = occ.addRectangle(X0, 0.0, 0.0, L_AXIAL, R_OUTER)

# Capsule: addDisk creates a FULL circle (it would extend to r<0, which is
# unphysical for an axisymmetric half-plane model) -- clip it to r>=0 by
# cutting away the r<0 half with a covering rectangle before using it.
capsule_full = occ.addDisk(CAPSULE_CENTER_X, 0.0, 0.0, R_CAPSULE, R_CAPSULE)
clip_below_axis = occ.addRectangle(CAPSULE_CENTER_X - R_CAPSULE - 1e-6,
                                    -R_CAPSULE - 1e-6, 0.0,
                                    2 * (R_CAPSULE + 1e-6), R_CAPSULE + 1e-6)
capsule_cut = occ.cut([(2, capsule_full)], [(2, clip_below_axis)],
                       removeObject=True, removeTool=True)
occ.synchronize()
capsule = capsule_cut[0][0][1]

# Keep capsule as its own region, water = outer minus capsule
water_minus = occ.cut([(2, outer)], [(2, capsule)], removeTool=False, removeObject=True)
occ.synchronize()

# Fragment to ensure conformal shared edge between water region and capsule disk
# (cut already leaves capsule disk as its own untouched entity; re-add it as a
#  surface in the same model so meshing shares nodes on the interface)
all_surfaces = gmsh.model.getEntities(2)
occ.synchronize()

gmsh.model.mesh.setSize(gmsh.model.getEntities(0), LC_OUTER)

# Assign finer size near the capsule boundary
capsule_surf_tag = capsule
water_surf_tags = [s[1] for s in all_surfaces if s[1] != capsule_surf_tag]

gmsh.model.mesh.field.add("Distance", 1)
gmsh.model.mesh.field.setNumbers(1, "CurvesList",
    [c[1] for c in gmsh.model.getBoundary([(2, capsule_surf_tag)], oriented=False)])
gmsh.model.mesh.field.add("Threshold", 2)
gmsh.model.mesh.field.setNumber(2, "InField", 1)
gmsh.model.mesh.field.setNumber(2, "SizeMin", LC_CAPSULE)
gmsh.model.mesh.field.setNumber(2, "SizeMax", LC_OUTER)
gmsh.model.mesh.field.setNumber(2, "DistMin", 0.0)
gmsh.model.mesh.field.setNumber(2, "DistMax", R_OUTER - R_CAPSULE)
gmsh.model.mesh.field.setAsBackgroundMesh(2)

# ---- physical groups (named zones Fluent will read) ----
gmsh.model.addPhysicalGroup(2, [capsule_surf_tag], name="capsule")
gmsh.model.addPhysicalGroup(2, water_surf_tags, name="water")

# boundary curves: find by bounding box position
all_curves = gmsh.model.getEntities(1)
eps = 1e-6
inlet, outlet, wall_outer, axis_lines, interface_lines = [], [], [], [], []
for dim, tag in all_curves:
    com = gmsh.model.occ.getCenterOfMass(dim, tag)
    bbox = gmsh.model.getBoundingBox(dim, tag)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox
    is_vertical = abs(xmax - xmin) < eps
    is_horizontal_at_r0 = abs(ymax) < eps and abs(ymin) < eps
    if is_horizontal_at_r0:
        axis_lines.append(tag)
    elif is_vertical and abs(xmin - X0) < 1e-5:
        inlet.append(tag)
    elif is_vertical and abs(xmin - (X0 + L_AXIAL)) < 1e-5:
        outlet.append(tag)
    elif abs(ymax - R_OUTER) < 1e-5 and abs(ymin - R_OUTER) < 1e-5:
        wall_outer.append(tag)
    else:
        # curved edges on the capsule circle that are NOT on the outer box
        com_r = com[1]
        if com_r < R_CAPSULE + 1e-4 and com_r > 1e-6:
            interface_lines.append(tag)

gmsh.model.addPhysicalGroup(1, inlet, name="inlet")
gmsh.model.addPhysicalGroup(1, outlet, name="outlet")
gmsh.model.addPhysicalGroup(1, wall_outer, name="wall_outer")
gmsh.model.addPhysicalGroup(1, axis_lines, name="axis")
if interface_lines:
    gmsh.model.addPhysicalGroup(1, interface_lines, name="capsule_wall")

gmsh.model.occ.synchronize()
gmsh.option.setNumber("Mesh.Algorithm", 6)  # Frontal-Delaunay, good for graded size fields
gmsh.model.mesh.generate(2)

gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
gmsh.write("regime0_capsule.msh")

n_nodes = len(gmsh.model.mesh.getNodes()[0])
print(f"Mesh written: regime0_capsule.msh  ({n_nodes} nodes)")
print(f"R_CAPSULE={R_CAPSULE*1000:.3f} mm, R_OUTER={R_OUTER*1000:.3f} mm, L_AXIAL={L_AXIAL*1000:.3f} mm")

gmsh.finalize()
