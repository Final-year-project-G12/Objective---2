"""
build_mesh_3d.py -- same Regime-0/RT57HC capsule-in-unit-cell geometry as
build_mesh.py, but extruded one cell thick in z (standard OpenFOAM
pseudo-2D convention: front/back faces get patch type "empty").
Fluent still uses the planar version (build_mesh.py); this one is for
OpenFOAM's gmshToFoam, which requires true 3D volume elements.

Run: python build_mesh_3d.py
Output: regime0_capsule_3d.msh
"""
import gmsh

gmsh.initialize()
gmsh.model.add("regime0_capsule_3d")

R_CAPSULE = 0.021022
R_OUTER = 1.7 * R_CAPSULE
L_AXIAL = 4 * (2 * R_CAPSULE)
X0 = -L_AXIAL / 2
THICKNESS = 0.002  # one-cell-thick slab in z, arbitrary small depth for pseudo-2D

LC_CAPSULE = R_CAPSULE / 18.0
LC_OUTER = R_OUTER / 10.0

occ = gmsh.model.occ
outer = occ.addRectangle(X0, 0.0, 0.0, L_AXIAL, R_OUTER)

# addDisk makes a FULL circle (extends to r<0, unphysical for an
# axisymmetric half-plane model) -- clip to r>=0 before using it.
capsule_full = occ.addDisk(0.0, 0.0, 0.0, R_CAPSULE, R_CAPSULE)
clip_below_axis = occ.addRectangle(-R_CAPSULE - 1e-6, -R_CAPSULE - 1e-6, 0.0,
                                    2 * (R_CAPSULE + 1e-6), R_CAPSULE + 1e-6)
capsule_cut = occ.cut([(2, capsule_full)], [(2, clip_below_axis)],
                       removeObject=True, removeTool=True)
occ.synchronize()
capsule_tool = capsule_cut[0][0][1]

# fragment (not cut): keeps both the water annulus AND the capsule disk as
# separate surfaces but forces them to share the SAME boundary curve at the
# interface (conformal). "cut" (tried first) instead gives each surface its
# own independent copy of the interface curve -- geometrically coincident
# but topologically distinct -- so the two sides mesh independently (92 vs
# 182 faces, mismatched) and splitMeshRegions cannot auto-detect them as a
# shared cellZone boundary, leaving the capsule side's interface untagged.
frag_out, frag_map = occ.fragment([(2, outer)], [(2, capsule_tool)])
occ.synchronize()
# after fragment, identify the two resulting surfaces by area (capsule disk
# is the small one; the rest -- water minus capsule -- is the large one)
areas = [(tag, occ.getMass(2, tag)) for dim, tag in frag_out]
areas.sort(key=lambda t: t[1])
capsule = areas[0][0]
water_surf = areas[1][0]

gmsh.model.mesh.setSize(gmsh.model.getEntities(0), LC_OUTER)
gmsh.model.mesh.field.add("Distance", 1)
gmsh.model.mesh.field.setNumbers(1, "CurvesList",
    [c[1] for c in gmsh.model.getBoundary([(2, capsule)], oriented=False)])
gmsh.model.mesh.field.add("Threshold", 2)
gmsh.model.mesh.field.setNumber(2, "InField", 1)
gmsh.model.mesh.field.setNumber(2, "SizeMin", LC_CAPSULE)
gmsh.model.mesh.field.setNumber(2, "SizeMax", LC_OUTER)
gmsh.model.mesh.field.setNumber(2, "DistMin", 0.0)
gmsh.model.mesh.field.setNumber(2, "DistMax", R_OUTER - R_CAPSULE)
gmsh.model.mesh.field.setAsBackgroundMesh(2)
gmsh.option.setNumber("Mesh.Algorithm", 6)
gmsh.model.mesh.generate(2)

# ---- extrude the 2 surfaces by one layer in z, one cell thick ----
all_surf_before = gmsh.model.getEntities(2)
ext = occ.extrude(all_surf_before, 0, 0, THICKNESS, numElements=[1], recombine=False)
occ.synchronize()

# ext is a list of (dim,tag) tuples: for each input surface, extrude returns
# [top_surface, volume, side1, side2, ...] in order
volumes = [e for e in ext if e[0] == 3]
top_surfaces = []
side_surfaces_all = []
idx = 0
per_input = len(ext) // len(all_surf_before)
for i, _ in enumerate(all_surf_before):
    chunk = ext[i*per_input:(i+1)*per_input]
    for e in chunk:
        if e[0] == 2:
            # first 2D entity in the chunk is the "top" cap; rest are sides
            pass
# classify the two volumes by size: capsule is much smaller than water
vol_info = []
for v in volumes:
    com = gmsh.model.occ.getCenterOfMass(3, v[1])
    mass = gmsh.model.occ.getMass(3, v[1])
    vol_info.append((v[1], mass, com))
vol_info.sort(key=lambda t: t[1])  # ascending volume: capsule is smaller
capsule_vol_tag = vol_info[0][0]
water_vol_tag = vol_info[1][0]

# Query each volume's own boundary faces directly (robust: avoids relying on
# tag-position heuristics, which previously missed the capsule side of the
# interface entirely -- gmshToFoam/splitMeshRegions need BOTH sides tagged
# "capsule_wall" so the interface becomes a real coupling patch on the
# capsule region too, instead of falling into an untagged defaultFaces patch).
capsule_boundary = [t for d, t in gmsh.model.getBoundary([(3, capsule_vol_tag)], oriented=False)]
water_boundary = [t for d, t in gmsh.model.getBoundary([(3, water_vol_tag)], oriented=False)]

eps = 1e-6
front_back, inlet, outlet, wall_outer, axis_faces, interface_faces = [], [], [], [], [], []

for tag in capsule_boundary:
    bbox = gmsh.model.getBoundingBox(2, tag)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox
    if abs(zmax - zmin) < 1e-5:
        front_back.append(tag)
    elif abs(ymax) < eps and abs(ymin) < eps:
        axis_faces.append(tag)  # capsule's flat diameter face sits on the symmetry axis
    else:
        interface_faces.append(tag)  # remaining capsule boundary is the curved interface

for tag in water_boundary:
    bbox = gmsh.model.getBoundingBox(2, tag)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox
    if abs(zmax - zmin) < 1e-5:
        front_back.append(tag)
    elif abs(ymax) < eps and abs(ymin) < eps:
        axis_faces.append(tag)
    elif abs(xmin - X0) < 1e-5 and abs(xmax - X0) < 1e-5:
        inlet.append(tag)
    elif abs(xmin - (X0 + L_AXIAL)) < 1e-5 and abs(xmax - (X0 + L_AXIAL)) < 1e-5:
        outlet.append(tag)
    elif abs(ymax - R_OUTER) < 1e-5:
        wall_outer.append(tag)
    else:
        interface_faces.append(tag)  # water's remaining boundary is the capsule interface

gmsh.model.addPhysicalGroup(3, [capsule_vol_tag], name="capsule")
gmsh.model.addPhysicalGroup(3, [water_vol_tag], name="water")
gmsh.model.addPhysicalGroup(2, inlet, name="inlet")
gmsh.model.addPhysicalGroup(2, outlet, name="outlet")
gmsh.model.addPhysicalGroup(2, wall_outer, name="wall_outer")
gmsh.model.addPhysicalGroup(2, axis_faces, name="axis")
gmsh.model.addPhysicalGroup(2, interface_faces, name="capsule_wall")
gmsh.model.addPhysicalGroup(2, front_back, name="frontAndBack")

gmsh.model.mesh.generate(3)
gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
gmsh.write("regime0_capsule_3d.msh")

print(f"3D mesh written. Volumes: capsule={vol_info[0][1]:.3e} m^3, water={vol_info[1][1]:.3e} m^3")
print(f"inlet faces={len(inlet)} outlet={len(outlet)} wall_outer={len(wall_outer)} "
      f"axis={len(axis_faces)} interface={len(interface_faces)} frontAndBack={len(front_back)}")

gmsh.finalize()
