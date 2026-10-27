"""
Parameterized version of build_mesh.py -- same verified geometry/meshing
approach (half-disk clip, graded sizing, zone classification), generalized
to take any regime's real capsule radius so Regimes 1 and 2 can reuse the
exact same, already-proven construction as Regime 0.

Usage: python build_mesh_regime.py <R_CAPSULE_m> <output_basename>
Example: python build_mesh_regime.py 0.022019247883429918 regime1_capsule
"""
import sys
import gmsh

R_CAPSULE = float(sys.argv[1])
OUT_BASENAME = sys.argv[2]

gmsh.initialize()
gmsh.model.add(OUT_BASENAME)

R_OUTER = 1.7 * R_CAPSULE
L_AXIAL = 4 * (2 * R_CAPSULE)
X0 = -L_AXIAL / 2
CAPSULE_CENTER_X = 0.0

LC_CAPSULE = R_CAPSULE / 18.0
LC_OUTER = R_OUTER / 10.0

occ = gmsh.model.occ

outer = occ.addRectangle(X0, 0.0, 0.0, L_AXIAL, R_OUTER)

capsule_full = occ.addDisk(CAPSULE_CENTER_X, 0.0, 0.0, R_CAPSULE, R_CAPSULE)
clip_below_axis = occ.addRectangle(CAPSULE_CENTER_X - R_CAPSULE - 1e-6,
                                    -R_CAPSULE - 1e-6, 0.0,
                                    2 * (R_CAPSULE + 1e-6), R_CAPSULE + 1e-6)
capsule_cut = occ.cut([(2, capsule_full)], [(2, clip_below_axis)],
                       removeObject=True, removeTool=True)
occ.synchronize()
capsule = capsule_cut[0][0][1]

water_minus = occ.cut([(2, outer)], [(2, capsule)], removeTool=False, removeObject=True)
occ.synchronize()

all_surfaces = gmsh.model.getEntities(2)
occ.synchronize()

gmsh.model.mesh.setSize(gmsh.model.getEntities(0), LC_OUTER)

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

gmsh.model.addPhysicalGroup(2, [capsule_surf_tag], name="capsule")
gmsh.model.addPhysicalGroup(2, water_surf_tags, name="water")

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
gmsh.option.setNumber("Mesh.Algorithm", 6)
gmsh.model.mesh.generate(2)

gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
gmsh.write(f"{OUT_BASENAME}.msh")

n_nodes = len(gmsh.model.mesh.getNodes()[0])
print(f"Mesh written: {OUT_BASENAME}.msh  ({n_nodes} nodes)")
print(f"R_CAPSULE={R_CAPSULE*1000:.3f} mm, R_OUTER={R_OUTER*1000:.3f} mm, L_AXIAL={L_AXIAL*1000:.3f} mm")

gmsh.finalize()
