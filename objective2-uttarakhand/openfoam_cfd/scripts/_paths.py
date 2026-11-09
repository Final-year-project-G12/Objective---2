"""
_paths.py -- locate the Objective-2 Uttarakhand project (the folder that holds
src/design/geometry.py, configs/ and data/) from objective2-uttarakhand/openfoam_cfd/scripts.

Adapted from the shared ../../../openfoam_cfd/scripts/_paths.py (Rajasthan): same lookup, but it finds
objective2-uttarakhand and reads the Uttarakhand PCM database. Override with the environment variable O2_PROJECT_ROOT.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_MARK = os.path.join("src", "design", "geometry.py")


def project_root():
    env = os.environ.get("O2_PROJECT_ROOT")
    if env and os.path.exists(os.path.join(env, _MARK)):
        return os.path.abspath(env)
    cur = HERE
    for _ in range(6):
        for cand in (cur, os.path.join(cur, "objective2-uttarakhand")):
            if os.path.exists(os.path.join(cand, _MARK)):
                return os.path.abspath(cand)
        cur = os.path.dirname(cur)
    raise SystemExit("cannot find the objective2-uttarakhand project (src/design/geometry.py); "
                     "set O2_PROJECT_ROOT")


def pcm_database():
    return os.path.join(project_root(), "data", "objective1", "pcm_database_uttarakhand.csv")


def wsl_distro():
    """WSL distribution that has OpenFOAM v2406 (the shared setup used Ubuntu-24.04)."""
    return os.environ.get("O2_WSL_DISTRO", "Ubuntu-24.04")


if __name__ == "__main__":
    print(project_root())
    print(pcm_database(), os.path.exists(pcm_database()))
    print(wsl_distro())
