"""
Ground-truth zone identification for a Fluent mesh-only case file, reading
the HDF5 structure directly (no Fluent launch needed). Generalizes the
manual investigation done for Regime 0 (which found 3_s_1=water,
3_s_2=capsule, 2_l_8=wall_outer, 2_l_11=inlet, 2_l_10=outlet,
2_l_9/2_l_7=axis(water side), 2_l_5=axis(capsule side), confirming names
are NOT assumed to transfer between regimes even though mesh topology is
identical).

Usage: python verify_zones.py <case_file.cas.h5>
"""
import sys
import h5py
import numpy as np

CASE_PATH = sys.argv[1]
f = h5py.File(CASE_PATH, "r")

cell_zt = f["meshes/1/cells/zoneTopology"]
cell_names = cell_zt["name"][()][0].decode().split(";")
cell_ids = cell_zt["id"][()]
cell_minid = cell_zt["minId"][()]
cell_maxid = cell_zt["maxId"][()]
print("=== Cell zones ===")
for i, name in enumerate(cell_names):
    print(f"  {name}: id={cell_ids[i]} range=[{cell_minid[i]},{cell_maxid[i]}] "
          f"ncells={cell_maxid[i]-cell_minid[i]+1}")

face_zt = f["meshes/1/faces/zoneTopology"]
face_names_raw = face_zt["name"][()][0].decode().split(";")
face_ids = face_zt["id"][()]
face_minid = face_zt["minId"][()]
face_maxid = face_zt["maxId"][()]
print("\n=== Face zones ===")
name_by_id = {}
range_by_name = {}
for i, name in enumerate(face_names_raw):
    fid = face_ids[i]
    lo, hi = int(face_minid[i]), int(face_maxid[i])
    name_by_id[fid] = name
    range_by_name[name] = (lo, hi)
    print(f"  {name}: id={fid} range=[{lo},{hi}] nfaces={hi-lo+1}")

# find the interface zone (contains "interface" in its name) and the two
# cell-zone id ranges, to determine which cell zone is water vs capsule
interface_name = next((n for n in face_names_raw if "interface" in n.lower()), None)
c0 = f["meshes/1/faces/c0/1"][()]

if interface_name:
    lo, hi = range_by_name[interface_name]
    seg_c0 = c0[lo - 1:hi]
    print(f"\nInterface zone '{interface_name}' c0 cell range: "
          f"[{seg_c0.min()}, {seg_c0.max()}]")
    # also check c1 sub-datasets for the matching range
    for key in f["meshes/1/faces/c1"].keys():
        d = f[f"meshes/1/faces/c1/{key}"]
        attrs = dict(d.attrs)
        if int(attrs.get("minId", [-1])[0]) == lo:
            vals = d[()]
            print(f"Interface zone c1 (other side) cell range: "
                  f"[{vals.min()}, {vals.max()}]  (c1/{key})")

# For each non-interior, non-interface face zone, report which cell-zone
# range its c0 neighbors fall into, plus x-position (for inlet/outlet) and
# y-position (for axis vs wall_outer).
coords = f["meshes/1/nodes/coords/12"][()].reshape(-1, 2)
nnodes = f["meshes/1/faces/nodes/1/nnodes"][()]
nodes = f["meshes/1/faces/nodes/1/nodes"][()]
offsets = np.concatenate([[0], np.cumsum(nnodes)])


def face_range_stats(lo, hi):
    xs, ys = [], []
    for fidx in range(lo - 1, hi):
        n0, n1 = offsets[fidx], offsets[fidx + 1]
        pts = coords[nodes[n0:n1] - 1]
        xs.append(pts[:, 0].mean())
        ys.append(pts[:, 1].mean())
    return np.mean(xs), np.min(ys), np.max(ys), np.mean(ys)


print("\n=== Boundary zone geometry/adjacency (excludes interior+interface) ===")
for name, (lo, hi) in range_by_name.items():
    if "interior" in name.lower() or name == interface_name:
        continue
    seg_c0 = c0[lo - 1:hi]
    xmean, ymin, ymax, ymean = face_range_stats(lo, hi)
    print(f"  {name}: c0 cellrange=[{seg_c0.min()},{seg_c0.max()}] "
          f"x_mean={xmean:.5f} y_range=[{ymin:.5f},{ymax:.5f}]")

f.close()
