"""
Reads the REAL written time-directory output (0.xxxx/capsule/T,
0.xxxx/water/T) from the actual chtMultiRegionFoam run in this folder and
plots capsule (PCM) mean temperature vs simulated time, plus a snapshot
scatter of the capsule temperature field at the latest available time.

This is a genuine result check -- it only reads files the solver itself
wrote, nothing is synthesized. Run after the background run has written at
least 2 time directories (ls -d 0.*/ to check).

Run: python plot_temperature_result.py
"""
import re
import glob
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def strip_header(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    return text


def read_internal_field(path):
    text = strip_header(open(path).read())
    m_uniform = re.search(r"internalField\s+uniform\s+([\-0-9.eE]+)\s*;", text)
    if m_uniform:
        return np.array([float(m_uniform.group(1))])
    m = re.search(r"internalField\s+nonuniform[^\n]*\n(\d+)\s*\n\(", text)
    n = int(m.group(1))
    body = text[m.end():]
    nums = re.findall(r"[\-0-9.eE]+", body)[:n]
    return np.array([float(x) for x in nums])


time_dirs = []
for d in glob.glob("0.*") + glob.glob("[1-9]*"):
    if os.path.isdir(d) and os.path.isfile(os.path.join(d, "capsule", "T")):
        try:
            time_dirs.append(float(d))
        except ValueError:
            pass
time_dirs = sorted(time_dirs)

if os.path.isfile("0/capsule/T"):
    time_dirs = [0.0] + time_dirs

times, capsule_mean, capsule_max, water_mean = [], [], [], []
for t in time_dirs:
    tdir = "0" if t == 0.0 else repr(t)
    if not os.path.isdir(tdir):
        # float repr may not match the directory name exactly; find it
        matches = [d for d in glob.glob("0.*") if abs(float(d) - t) < 1e-12]
        tdir = matches[0] if matches else tdir
    cpath = os.path.join(tdir, "capsule", "T")
    wpath = os.path.join(tdir, "water", "T")
    if not os.path.isfile(cpath):
        continue
    cT = read_internal_field(cpath)
    times.append(t)
    capsule_mean.append(cT.mean())
    capsule_max.append(cT.max())
    if os.path.isfile(wpath):
        wT = read_internal_field(wpath)
        water_mean.append(wT.mean())
    else:
        water_mean.append(np.nan)

times = np.array(times)
capsule_mean = np.array(capsule_mean) - 273.15
capsule_max = np.array(capsule_max) - 273.15
water_mean = np.array(water_mean) - 273.15

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(times, capsule_mean, "o-", color="#c2531f", label="PCM (capsule) mean T")
ax.plot(times, capsule_max, "x--", color="#a83226", label="PCM (capsule) max T")
ax.plot(times, water_mean, "o-", color="#1b5e63", label="water mean T")
ax.axhline(56.5, color="gray", linestyle=":", lw=1, label="RT57HC Tm = 56.5 C")
ax.axhline(25.0, color="black", linestyle=":", lw=0.8, label="initial PCM temp = 25 C")
ax.set_xlabel("simulated time (s)")
ax.set_ylabel("temperature (C)")
ax.set_title("Regime 0 / RT57HC conjugate heat transfer -- real chtMultiRegionFoam output\n(sensible heating only -- no latent heat in this OpenFOAM case, see thermophysicalProperties note)")
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig("temperature_result.png", dpi=150, bbox_inches="tight")

print(f"{len(times)} real time snapshots read, t = {times.min():.5f} to {times.max():.5f} s")
print(f"PCM mean T:  {capsule_mean[0]:.3f} C -> {capsule_mean[-1]:.3f} C")
print(f"PCM max T:   {capsule_max[0]:.3f} C -> {capsule_max[-1]:.3f} C")
print(f"Water mean T: {water_mean[0]:.3f} C -> {water_mean[-1]:.3f} C")
print("Saved temperature_result.png")
