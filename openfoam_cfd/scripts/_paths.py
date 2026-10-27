"""
_paths.py -- locate the Objective-2 Rajasthan project (the folder that holds
src/design/geometry.py, configs/ and data/) no matter where openfoam_cfd/ lives.

openfoam_cfd/ was first created INSIDE objective2-rajasthan/ and later moved next
to it (Objective---2/openfoam_cfd). Both layouts work. Override with the
environment variable O2_PROJECT_ROOT.
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
        for cand in (cur, os.path.join(cur, "objective2-rajasthan")):
            if os.path.exists(os.path.join(cand, _MARK)):
                return os.path.abspath(cand)
        cur = os.path.dirname(cur)
    raise SystemExit("cannot find the objective2-rajasthan project (src/design/geometry.py); "
                     "set O2_PROJECT_ROOT")


def pcm_database():
    return os.path.join(project_root(), "data", "objective1", "pcm_database_rajasthan.csv")


if __name__ == "__main__":
    print(project_root())
    print(pcm_database(), os.path.exists(pcm_database()))
