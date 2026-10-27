"""
scripts/g12_verify_docs.py
=============================
G12 - checks that the files and functions the redesign documents name actually exist. For every `backticked` token in the listed
documents that looks like a path (contains a slash or ends in a known extension) it expands {a,b} and * and requires at least one
match under the project folder, docs/, docs/redesign/ or results/redesign/. For tokens of the form `path.py: name` or
`path.py: name(...)` it also requires `name` to be defined or assigned in that file. Placeholders such as <c> and <regime> are
turned into wildcards. Prints every miss and exits with status 1 if any.
Usage: python scripts/g12_verify_docs.py
"""

import glob
import itertools
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = [ROOT / "docs/redesign" / n for n in ("README.md", "01_MODEL_AND_METRICS.md", "02_WEATHER_AND_DESIGN_SPACE.md",
                                              "03_OPTIMISATION_PIPELINE.md", "04_RESULTS.md", "05_LIMITATIONS_AND_OPEN_ITEMS.md",
                                              "06_OBJECTIVE3_HANDOFF.md")]
EXT = (".py", ".csv", ".yaml", ".json", ".md", ".lock", ".txt", ".sha256")
BASES = [ROOT.parent.parent.parent, ROOT, ROOT / "docs", ROOT / "docs/redesign", ROOT / "results/redesign", ROOT / "results", ROOT / "src", ROOT / "scripts"]
SKIP = {"out.csv"}


def expand(tok):
    m = re.search(r"\{([^}]*)\}", tok)
    if not m:
        return [tok]
    return [x for opt in m.group(1).split(",") for x in expand(tok[:m.start()] + opt + tok[m.end():])]


def exists(tok):
    tok = re.sub(r"<[^>]*>", "*", tok)
    for t in expand(tok):
        t = t.rstrip("/").replace("*", "*")
        if not any(glob.glob(str(b / t)) for b in BASES):
            return False
    return True


def defined(path, name):
    for b in BASES:
        for f in glob.glob(str(b / path)):
            txt = Path(f).read_text(encoding="utf-8", errors="replace")
            if re.search(rf"^\s*(def|class)\s+{re.escape(name)}\b|^\s*{re.escape(name)}\s*[:=]", txt, re.M):
                return True
    return False


def main():
    miss, n = [], 0
    for d in DOCS:
        text = d.read_text(encoding="utf-8")
        for tok in re.findall(r"`([^`\n]+)`", text):
            tok = tok.strip()
            m = re.match(r"^([\w./{},*<>-]+\.py):\s*([A-Za-z_]\w*)", tok)
            if m:
                n += 1
                if not exists(m.group(1)):
                    miss.append((d.name, tok, "file missing"))
                elif not defined(m.group(1), m.group(2)):
                    miss.append((d.name, tok, "name not defined in file"))
                continue
            first = tok.split()[0] if tok.split() else tok
            if first.startswith(("python", "PYTHONPATH", "G9_")):          # command lines: check script paths inside
                for part in tok.split():
                    if part.endswith(".py"):
                        n += 1
                        if not exists(part):
                            miss.append((d.name, part, "script missing"))
                continue
            if tok in SKIP or " " in tok or tok.startswith(("http", "-")):
                continue
            if "/" in tok or tok.endswith(EXT):
                if re.search(r"[=()]", tok):
                    continue
                n += 1
                if not exists(tok):
                    miss.append((d.name, tok, "path not found"))
    print("checked", n, "references;", len(miss), "missing")
    for m in miss:
        print("  MISSING", m)
    sys.exit(1 if miss else 0)


if __name__ == "__main__":
    main()
