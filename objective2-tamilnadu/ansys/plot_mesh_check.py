"""
Visual verification of the Regime-0/RT57HC capsule mesh actually used by
the Fluent and OpenFOAM cases -- renders the real node/element data read
back from the .msh files (not a schematic), so the plot is a direct check
of what the solvers import, not an illustration drawn separately from it.

Produces mesh_verification.png: the corrected half-disk capsule (used by
both solvers) plotted next to the original buggy full-circle version, so
the fix is visible, not just asserted.

Run: python plot_mesh_check.py
"""
import gmsh
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

R_CAPSULE = 0.021022
R_OUTER = 1.7 * R_CAPSULE


def read_mesh_triangles(msh_path):
    gmsh.initialize()
    gmsh.open(msh_path)
    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    coord_map = {t: node_coords[3 * i:3 * i + 2] for i, t in enumerate(node_tags)}

    groups = {}
    for dim, tag in gmsh.model.getPhysicalGroups(2):
        name = gmsh.model.getPhysicalName(dim, tag)
        tris = []
        for ent in gmsh.model.getEntitiesForPhysicalGroup(dim, tag):
            etypes, etags, enodes = gmsh.model.mesh.getElements(2, ent)
            for et, en in zip(etypes, enodes):
                if et == 2:  # 3-node triangle
                    en = np.array(en).reshape(-1, 3)
                    for tri in en:
                        tris.append([coord_map[n] for n in tri])
        groups[name] = tris

    boundary_edges = {}
    for dim, tag in gmsh.model.getPhysicalGroups(1):
        name = gmsh.model.getPhysicalName(dim, tag)
        segs = []
        for ent in gmsh.model.getEntitiesForPhysicalGroup(dim, tag):
            etypes, etags, enodes = gmsh.model.mesh.getElements(1, ent)
            for et, en in zip(etypes, enodes):
                if et == 1:  # 2-node line
                    en = np.array(en).reshape(-1, 2)
                    for seg in en:
                        segs.append([coord_map[n] for n in seg])
        boundary_edges[name] = segs

    gmsh.finalize()
    return groups, boundary_edges


def build_buggy_full_circle_reference():
    """The pre-fix geometry: addDisk's full circle, unclipped -- for the
    side-by-side comparison only (not read from any current mesh file,
    since the fix already regenerated regime0_capsule.msh correctly)."""
    theta = np.linspace(0, 2 * np.pi, 64)
    x = R_CAPSULE * np.cos(theta)
    y = R_CAPSULE * np.sin(theta)
    return x, y


fig, axes = plt.subplots(1, 2, figsize=(13, 6))

# ---- LEFT: the bug, illustrated for comparison (not a live mesh) ----
ax = axes[0]
L_AXIAL = 4 * (2 * R_CAPSULE)
X0 = -L_AXIAL / 2
ax.add_patch(plt.Rectangle((X0, 0), L_AXIAL, R_OUTER, fill=False, edgecolor="#1b5e63", lw=1.2))
xc, yc = build_buggy_full_circle_reference()
ax.plot(xc, yc, color="#c2531f", lw=1.6)
ax.fill(xc, yc, color="#f4ded1", alpha=0.6)
ax.axhline(0, color="black", lw=0.8, linestyle=":")
ax.axhspan(-R_CAPSULE * 1.15, 0, color="#a83226", alpha=0.12)
ax.text(0, -R_CAPSULE * 0.75, "r < 0 : physically\nmeaningless for an\naxisymmetric solver",
        ha="center", va="center", fontsize=9, color="#a83226")
ax.set_xlim(X0 * 1.1, (X0 + L_AXIAL) * 1.1)
ax.set_ylim(-R_CAPSULE * 1.3, R_OUTER * 1.15)
ax.set_aspect("equal")
ax.set_title("BEFORE FIX (bug)\naddDisk() creates a full circle,\nextending below the symmetry axis", fontsize=11)
ax.set_xlabel("x (m)")
ax.set_ylabel("r (m)")

# ---- RIGHT: the real, corrected mesh, read back from regime0_capsule.msh ----
ax = axes[1]
groups, edges = read_mesh_triangles("regime0_capsule.msh")

color_map = {"water": "#dcebe9", "capsule": "#f4ded1"}
for name, tris in groups.items():
    verts = [np.array(t) for t in tris]
    pc = PolyCollection(verts, facecolor=color_map.get(name, "#eee"),
                         edgecolor="#b9b2a0", linewidth=0.15)
    ax.add_collection(pc)

edge_style = {
    "inlet": ("#1b5e63", 3.0),
    "outlet": ("#1b5e63", 3.0),
    "wall_outer": ("#5b564c", 2.2),
    "axis": ("black", 1.4),
    "capsule_wall": ("#c2531f", 2.0),
}
for name, segs in edges.items():
    color, lw = edge_style.get(name, ("#999", 1.0))
    for seg in segs:
        seg = np.array(seg)
        ax.plot(seg[:, 0], seg[:, 1], color=color, lw=lw, solid_capstyle="round")

ax.set_xlim(X0 * 1.1, (X0 + L_AXIAL) * 1.1)
ax.set_ylim(-R_CAPSULE * 0.3, R_OUTER * 1.15)
ax.set_aspect("equal")
ax.set_title("AFTER FIX (current, verified mesh)\nregime0_capsule.msh -- capsule clipped to r>=0,\nread back directly from the actual mesh file", fontsize=11)
ax.set_xlabel("x (m)")
ax.set_ylabel("r (m)")

handles = [plt.Line2D([0], [0], color=c, lw=lw, label=n)
           for n, (c, lw) in edge_style.items()]
ax.legend(handles=handles, loc="upper right", fontsize=8, framealpha=0.9)

fig.suptitle("Regime 0 / RT57HC capsule mesh -- geometry verification (real data, not illustrative)", fontsize=12, y=1.02)
fig.tight_layout()
fig.savefig("mesh_verification.png", dpi=160, bbox_inches="tight")
print("Saved mesh_verification.png")

# ---- sanity assertions, printed so this is a real check, not just a picture ----
all_y = []
for tris in groups.values():
    for t in tris:
        for pt in t:
            all_y.append(pt[1])
all_y = np.array(all_y)
print(f"Mesh y (radius) range: [{all_y.min():.6e}, {all_y.max():.6e}]")
assert all_y.min() >= -1e-9, "FAIL: mesh still contains r<0 geometry"
print("PASS: no part of the mesh extends below r=0 (axis).")

capsule_tris = groups.get("capsule", [])
capsule_area = 0.0
for t in capsule_tris:
    (x1, y1), (x2, y2), (x3, y3) = t
    capsule_area += abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)) / 2
expected_half_disk_area = 0.5 * np.pi * R_CAPSULE ** 2
print(f"Capsule cross-section area (meshed): {capsule_area:.6e} m^2")
print(f"Expected half-disk area:             {expected_half_disk_area:.6e} m^2")
print(f"Relative error: {abs(capsule_area - expected_half_disk_area) / expected_half_disk_area * 100:.2f}%")
assert abs(capsule_area - expected_half_disk_area) / expected_half_disk_area < 0.03, \
    "FAIL: capsule area does not match the expected half-disk (within 3% mesh-discretization tolerance)"
print("PASS: capsule cross-section area matches the expected half-disk within mesh-discretization tolerance.")
