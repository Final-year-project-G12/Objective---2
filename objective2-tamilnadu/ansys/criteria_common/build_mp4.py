"""ansys/criteria_common/build_mp4.py -> MP4 videos of the 7 criteria (Fluent whole-tank discharge).

Uses the PNG frames Fluent saved (criteria_*/figures/frames, one every 5 simulated minutes, 0-60 min).
Needs: pip install imageio imageio-ffmpeg pillow
Writes:
  criteria_*/figures/criteria_N_<name>.mp4      temperature | liquid fraction, side by side, with design caption
  videos/COMPARE_temperature_all_criteria.mp4   all 7 designs in one grid (temperature)
  videos/COMPARE_liquid_fraction_all_criteria.mp4
"""
import json
import re
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ANSYS = Path(__file__).resolve().parents[1]
OUT = ANSYS / "videos"
OUT.mkdir(exist_ok=True)
FPS, HOLD = 5, 4          # each 5-minute frame is shown 4/5 s
SIM_MIN_PER_FRAME = 5


def font(sz, bold=False):
    for n in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def minute(p):
    return int(re.search(r"_(\d+)", p.stem).group(1))


def frames(folder, field):
    fs = [f for f in (folder / "figures" / "frames").glob(f"{field}_*.png") if "FINAL" not in f.stem]
    return sorted(fs, key=minute)


def caption(c, n):
    d = c["design"]
    return (f"{c['title']}   |   R_in {d['R_in']*1000:.0f} mm, {n['N']} capsules, PCM {n['pcm_mass_kg']:.1f} kg, "
            f"flow {d['flow']:.3f} kg/s, {d['arrangement']}   |   gain {n['g_window_kWh_yr']:.0f} kWh/yr "
            f"({n['pct_of_optimal_gain']:.0f}% of optimal)")


def write(path, frame_list):
    with imageio.get_writer(path, fps=FPS, codec="libx264", quality=8, macro_block_size=2,
                            ffmpeg_params=["-pix_fmt", "yuv420p"]) as w:
        for im in frame_list:
            a = np.asarray(im.convert("RGB"))
            for _ in range(HOLD):
                w.append_data(a)
    print("wrote", path.relative_to(ANSYS), f"({len(frame_list)*HOLD/FPS:.1f} s)")


def banner(w, text, sub, h=70):
    b = Image.new("RGB", (w, h), (30, 30, 40))
    d = ImageDraw.Draw(b)
    d.text((14, 8), text, fill="white", font=font(24, True))
    d.text((14, 40), sub, fill=(200, 200, 210), font=font(18))
    return b


def per_criteria(folder, c, n):
    t, l = frames(folder, "temp"), frames(folder, "liqfrac")
    out = []
    for i, (a, b) in enumerate(zip(t, l)):
        A, B = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
        w, h = A.size
        top = banner(2 * w, caption(c, n)[:200], f"Fluent 2-D tank discharge, capsules start melted at 70 C in 30 C water, no sun   |   t = {i*SIM_MIN_PER_FRAME} min  (left: temperature, right: liquid fraction of PCM)")
        canvas = Image.new("RGB", (2 * w, h + top.height), "white")
        canvas.paste(top, (0, 0))
        canvas.paste(A, (0, top.height))
        canvas.paste(B, (w, top.height))
        out.append(canvas)
    write(folder / "figures" / f"{folder.name}.mp4", out)


def grid(field, label, items):
    cw, ch = 480, 360
    cols, rows = 4, 2
    seqs = [frames(f, field) for f, _, _ in items]
    nfr = min(len(s) for s in seqs)
    out = []
    for i in range(nfr):
        canvas = Image.new("RGB", (cols * cw, rows * ch + 60), "white")
        canvas.paste(banner(cols * cw, f"All 7 designs side by side: {label}", f"t = {i*SIM_MIN_PER_FRAME} min after the sun goes off", 60), (0, 0))
        for k, ((f, c, n), s) in enumerate(zip(items, seqs)):
            im = Image.open(s[i]).convert("RGB").resize((cw, ch - 28))
            x, y = (k % cols) * cw, 60 + (k // cols) * ch
            canvas.paste(im, (x, y + 28))
            d = ImageDraw.Draw(canvas)
            d.rectangle([x, y, x + cw, y + 28], fill=(235, 235, 240))
            d.text((x + 6, y + 4), f"{c['title'][:34]}  {n['pct_of_optimal_gain']:.0f}%", fill="black", font=font(15, True))
        d = ImageDraw.Draw(canvas)
        x, y = 3 * cw, 60 + ch
        d.text((x + 10, y + 20), "% = yearly extra evening heat\nvs the optimum (100%).", fill="black", font=font(18))
        d.text((x + 10, y + 90), "Same Fluent set-up for all 7;\nonly capsule size / number\ndiffer (2-D slice).", fill=(80, 80, 80), font=font(16))
        out.append(canvas)
    write(OUT / f"COMPARE_{label.replace(' ', '_')}_all_criteria.mp4", out)


def main():
    items = []
    for f in sorted(ANSYS.glob("criteria_[0-9]_*")):
        c = json.loads((f / "criteria.json").read_text())
        n = json.loads((f / "node_model_results.json").read_text())
        items.append((f, c, n))
        per_criteria(f, c, n)
    grid("temp", "temperature", items)
    grid("liqfrac", "liquid_fraction", items)


if __name__ == "__main__":
    main()
