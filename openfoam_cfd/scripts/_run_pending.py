"""Runs the verification + full DOE batches sequentially (log: results/_pending.log)."""
import os, subprocess, sys, copy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
def sh(args):
    print(">>", " ".join(args), flush=True)
    subprocess.run([sys.executable] + args, cwd=HERE, check=False)
sh(["run_doe.py", "--mode", "sens", "--workers", "6"])
sh(["run_doe.py", "--mode", "doe", "--n-per-pcm", "16", "--workers", "8"])
sh(["run_doe.py", "--mode", "conduction", "--n-per-pcm", "16", "--workers", "8"])
sh(["cfd_calibrated_greybox.py", "--workers", "8"])
print("ALL DONE", flush=True)
