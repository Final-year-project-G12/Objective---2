"""ansys/criteria_common/build_gifs.py -> each criteria_*/figures/{temp,liqfrac}_video.gif
No ffmpeg on this machine, so the frames/*.png Fluent saved (every --frame-every minutes) are
stitched into an animated GIF with Pillow only. Run after a Fluent batch that used --frame-every.
"""
import re
from pathlib import Path

from PIL import Image

ANSYS = Path(__file__).resolve().parents[1]


def natural_minute(p):
    m = re.search(r"_(\d+)", p.stem)
    return int(m.group(1)) if m else 0


def build(folder, field, duration_ms=450):
    frames_dir = folder / "figures" / "frames"
    files = sorted(frames_dir.glob(f"{field}_*.png"), key=natural_minute)
    if not files:
        return None
    imgs = [Image.open(f).convert("P", palette=Image.ADAPTIVE) for f in files]
    out = folder / "figures" / f"{field}_video.gif"
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=duration_ms, loop=0)
    return out, len(files)


def main():
    for f in sorted(ANSYS.glob("criteria_[0-9]_*")):
        for field in ("temp", "liqfrac"):
            r = build(f, field)
            if r:
                print(f"{f.name:32s} {field:8s} {r[0].name}  ({r[1]} frames)")
            else:
                print(f"{f.name:32s} {field:8s} NO FRAMES")


if __name__ == "__main__":
    main()
