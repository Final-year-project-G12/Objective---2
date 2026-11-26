"""
scripts/g12_verify_docs.py
=============================
G12 - checks that the files and functions the rework documents name actually exist. For every `backticked` token in the listed
documents that looks like a path (contains a slash or ends in a known extension) it expands {a,b} and * and requires at least one
match under the project folder, docs/, docs/ or results/. For tokens of the form `path.py: name` or
`path.py: name(...)` it also requires `name` to be defined or assigned in that file. Placeholders such as <c> and <regime> are
turned into wildcards. Prints every miss and exits with status 1 if any.
Usage: python scripts/g12_verify_docs.py
"""

import glob
import itertools
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The seven numbered filenames this list used to carry (01_MODEL_AND_METRICS.md
# ... 06_OBJECTIVE3_HANDOFF.md) are the RAJASTHAN document set. Tamil Nadu's
# docs were never given those names, so this stage was checking a doc tree that
# does not exist here and could not have passed. Pointed at the real files.
# OVERVIEW.md ADDED 2026-11-09. It is the primary current account of what
# Objective 2 does and found -- docs/README now tells readers to start there
# rather than with RESULTS.md, which carries its own superseded banner -- yet
# it was the one top-level document whose paths nothing checked.
# SIMULATOR_AND_CFD.md and REFERENCES.md added for the same reason.
# docs/CORRECTIONS.md is deliberately NOT in this list: it is a history
# document whose job is to name files that were deleted, renamed or never
# written, and most of its path-like tokens are prose (`g9_s4/s5`,
# `x.cgns/.msh`, elided `..._v2.json`) rather than references to resolve.
DOCS = [ROOT / "README.md", ROOT / "OVERVIEW.md"] + [ROOT / "docs" / n for n in (
    "RESULTS.md", "CFD_VERIFICATION.md", "HOW_TO_RUN.md",
    "DATA_REFERENCE.md", "RAJASTHAN_METHOD_PORT_PROGRESS.md",
    "SIMULATOR_AND_CFD.md", "REFERENCES.md")]
EXT = (".py", ".csv", ".yaml", ".json", ".md", ".lock", ".txt", ".sha256")
# ROOT.parent.parent.parent used to reach the outer project when this tree was
# rajmethod/; after the 2026-10-30 promotion it would escape three levels ABOVE
# the project, so referenced paths are resolved against the project itself.
# The Objective-1 tree is a sibling of this project, and DATA_REFERENCE.md
# exists to document where Objective 1's frozen outputs came from -- so its
# scripts are legitimately referenced from here and must be resolvable.
O1_ROOT = ROOT.parent / "tamilnadu_pipeline"
# The OUTER project (jammalamadugu/) holds sibling trees the docs legitimately
# name: Github/PCM-Selection-ML-model/pcm_shared_config.py is the real source of
# T_DELIVERY_C/TM_TARGET_C, and Github/Objective---2/ is the Rajasthan original
# this method was ported from. Added 2026-11-09 -- without it, correct
# cross-repo references were reported missing.
OUTER = ROOT.parent.parent
BASES = [ROOT, ROOT / "docs", ROOT / "results", ROOT / "src", ROOT / "scripts",
         ROOT / "ansys", O1_ROOT, O1_ROOT / "scripts", O1_ROOT / "data",
         OUTER, OUTER / "Github", ROOT.parent]
SKIP = {"out.csv"}
# A token that is ONLY an extension (`.csv`, `.txt`, `.md`) is prose about a
# file FORMAT, not a path -- docs legitimately write "the `.txt` copy". This
# used to be the single hardcoded ".csv" entry. (2026-11-10)
BARE_EXT = re.compile(r"^\.\w+$")


def expand(tok):
    m = re.search(r"\{([^}]*)\}", tok)
    if not m:
        return [tok]
    return [x for opt in m.group(1).split(",") for x in expand(tok[:m.start()] + opt + tok[m.end():])]


# Built once: every file and directory under the project, except the archive
# and caches, indexed by name and by every trailing path fragment. The six
# BASES alone could not resolve a bare filename the docs mention in prose
# (constraints.py lives at src/design/constraints.py, which is under no base),
# so 236 paths that DO exist were reported missing. This resolves them without
# weakening the check: a path that is genuinely absent still fails.
_INDEX = None


def _index():
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    # archive/ IS indexed: nothing there was deleted, only retired, so a doc
    # that names a retired file is making a true statement about where it is.
    # Excluding it reported 60-odd paths missing that are present on disk.
    skip = {"__pycache__", ".git", ".pytest_cache", "node_modules", "interactive"}
    idx = set()
    roots = [ROOT] + ([O1_ROOT] if O1_ROOT.exists() else [])
    for root in roots:
      for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        rel = Path(dirpath).relative_to(root)
        for name in list(filenames) + list(dirnames):
            parts = (rel / name).parts
            for i in range(len(parts)):
                idx.add("/".join(parts[i:]))
    _INDEX = idx
    return idx


def exists(tok):
    tok = re.sub(r"<[^>]*>", "*", tok)
    # DOCUMENTATION PLACEHOLDERS (fix 2026-11-09). `{state}`, `{k}`, `{year}`,
    # `{point_id}`, `{thing}` and friends are placeholders meaning "any value",
    # exactly like <c> above -- but expand() below only understands BRACE
    # ALTERNATION `{a,b}`. A single-token brace has no comma, so expand()
    # substituted the placeholder NAME literally and looked for a file called
    # e.g. "climate_signature_state.csv", which of course does not exist. That
    # alone accounted for ~25 of the reported misses, every one of them a false
    # positive against a correctly written document. A brace containing no comma
    # is now a wildcard; `{a,b}` alternation still works unchanged.
    tok = re.sub(r"\{[^{},]*\}", "*", tok)
    # "..." in a path is an elision in prose ("point_years/.../cluster2_x.csv"),
    # not a literal directory. Same treatment.
    tok = tok.replace("/.../", "/*/").replace("...", "*")
    # A doc naming THIS project by folder ("objective2_design_optimization/data/")
    # is making a correct statement, but the bases all resolve INSIDE the project,
    # so the prefix never matched. Strip our own folder name. (2026-11-09)
    for own in (ROOT.name + "/", O1_ROOT.name + "/"):
        if tok.startswith(own):
            tok = tok[len(own):] or "."
    # "regime{0,1,2}_v3_capsule.cgns/.msh" is prose for "...cgns and ...msh",
    # not a directory called x.cgns. Check only the first form.
    if "/." in tok and not tok.endswith("/"):
        head = tok.split("/.")[0]
        if "." in Path(head).name:
            tok = head
    for t in expand(tok):
        t = t.rstrip("/")
        if any(glob.glob(str(b / t)) for b in BASES):
            continue
        norm = t.replace("\\", "/").lstrip("./")
        if norm in _index():
            continue
        if "*" in norm:                      # a glob the bases missed
            import fnmatch
            if any(fnmatch.fnmatch(k, norm) for k in _index()):
                continue
        return False
    return True


def defined(path, name):
    for b in BASES:
        for f in glob.glob(str(b / path)):
            txt = Path(f).read_text(encoding="utf-8", errors="replace")
            if re.search(rf"^\s*(def|class)\s+{re.escape(name)}\b|^\s*{re.escape(name)}\s*[:=]", txt, re.M):
                return True
    return False


# A document that says a file is GONE is making a true statement, and should not
# be forced to point at something that exists. Rather than silently skipping such
# paths, the check requires the doc to SAY SO on the same line -- so "genuinely
# missing" and "deliberately recorded as deleted" stay distinguishable, and a
# path can only be excused by a sentence a reader also sees. (2026-11-09)
GONE = re.compile(r"deleted|removed|retired|renamed|no longer exist|never written|"
                  r"not kept|superseded|does not exist|was never|not produced|"
                  r"not present",
                  re.I)


def main():
    miss, n = [], 0
    for d in DOCS:
        text = d.read_text(encoding="utf-8")
        # Collect EVERY line each token appears on, not just the first: a doc
        # often names a path in passing and then states, on another line, that
        # it is gone. Declaring it once is enough.
        line_of = {}
        for ln in text.split("\n"):
            for t in re.findall(r"`([^`\n]+)`", ln):
                line_of.setdefault(t.strip(), []).append(ln)
        for tok in re.findall(r"`([^`\n]+)`", text):
            tok = tok.strip()
            if any(GONE.search(ln) for ln in line_of.get(tok, [])):
                continue
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
            if tok in SKIP or BARE_EXT.match(tok) or " " in tok or tok.startswith(("http", "-")):
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
