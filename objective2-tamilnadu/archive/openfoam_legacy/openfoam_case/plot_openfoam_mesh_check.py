"""
Visual verification of the ACTUAL OpenFOAM mesh (constant/water/polyMesh,
constant/capsule/polyMesh) -- parses OpenFOAM's own ascii points/faces/
boundary files directly, not the upstream gmsh source, so this checks what
chtMultiRegionFoam itself reads.

Confirms the water_to_capsule / capsule_to_water coupling patches are
geometrically coincident (the bug this fixed: an earlier version had the
capsule side missing/mismatched, landing in an untagged defaultFaces patch
instead of a real coupling patch).

Run inside the openfoam conda env (needs numpy/matplotlib - same Windows
Python used for gmsh works fine since this only reads plain text files):
  python plot_openfoam_mesh_check.py
"""
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def strip_foam_header(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    return text


def read_points(path):
    text = strip_foam_header(open(path).read())
    m = re.search(r"\n(\d+)\s*\n\(", text)
    n = int(m.group(1))
    body = text[m.end():]
    nums = re.findall(r"\(([^)]*)\)", body)[:n]
    pts = np.array([[float(x) for x in row.split()] for row in nums])
    return pts


def read_faces(path):
    text = strip_foam_header(open(path).read())
    m = re.search(r"\n(\d+)\s*\n\(", text)
    n = int(m.group(1))
    body = text[m.end():]
    faces = []
    # format: N(idx idx idx ...)
    for mm in re.finditer(r"(\d+)\((.*?)\)", body):
        faces.append([int(x) for x in mm.group(2).split()])
        if len(faces) == n:
            break
    return faces


def read_boundary(path):
    text = strip_foam_header(open(path).read())
    patches = {}
    for m in re.finditer(r"(\w+)\s*\{([^}]*)\}", text):
        name, body = m.group(1), m.group(2)
        nf = re.search(r"nFaces\s+(\d+);", body)
        sf = re.search(r"startFace\s+(\d+);", body)
        if nf and sf:
            patches[name] = (int(sf.group(1)), int(nf.group(1)))
    return patches


def patch_face_centroids(region_dir, patch_name):
    pts = read_points(f"{region_dir}/points")
    faces = read_faces(f"{region_dir}/faces")
    boundary = read_boundary(f"{region_dir}/boundary")
    start, nfaces = boundary[patch_name]
    cents = []
    for fi in range(start, start + nfaces):
        face_pts = pts[faces[fi]]
        cents.append(face_pts.mean(axis=0))
    return np.array(cents)


fig, ax = plt.subplots(1, 1, figsize=(8, 6))

water_cents = patch_face_centroids("constant/water/polyMesh", "water_to_capsule")
capsule_cents = patch_face_centroids("constant/capsule/polyMesh", "capsule_to_water")

ax.scatter(water_cents[:, 0], water_cents[:, 1], s=14, c="#1b5e63", marker="o",
           label=f"water_to_capsule face centroids (n={len(water_cents)})", alpha=0.8)
ax.scatter(capsule_cents[:, 0], capsule_cents[:, 1], s=36, c="#c2531f", marker="x",
           label=f"capsule_to_water face centroids (n={len(capsule_cents)})", alpha=0.8)

ax.set_aspect("equal")
ax.set_xlabel("x (m)")
ax.set_ylabel("y (m)")
ax.set_title("OpenFOAM coupling interface -- read directly from\nconstant/{water,capsule}/polyMesh (actual solver input)")
ax.legend(loc="upper right", fontsize=9)
fig.tight_layout()
fig.savefig("openfoam_interface_check.png", dpi=160, bbox_inches="tight")
print("Saved openfoam_interface_check.png")

# ---- quantitative check: every capsule-side face centroid should land
# close to a water-side face centroid (same geometric interface) ----
from scipy.spatial import cKDTree
tree = cKDTree(water_cents)
dist, _ = tree.query(capsule_cents)
print(f"water_to_capsule faces: {len(water_cents)}")
print(f"capsule_to_water faces: {len(capsule_cents)}")
print(f"max nearest-neighbor distance (capsule centroid -> nearest water centroid): {dist.max():.3e} m")
print(f"mean nearest-neighbor distance: {dist.mean():.3e} m")
assert dist.max() < 2e-4, "FAIL: interface faces are not geometrically coincident"
print("PASS: capsule_to_water and water_to_capsule faces are geometrically coincident (real mappedWall coupling).")
