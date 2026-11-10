"""
src/simulation/node_layout.py
================================
Where the capsules sit in the node stack. Deliberately dependency-light:
numpy only.

WHY IT IS ITS OWN MODULE. `_capsule_node_band` used to live in
tank_model_multinode.py, so the numba kernel imported that module just to
reach it -- and that module imports `sklearn.isotonic` for its reference
PAV implementation. Measured: `import sklearn.isotonic` costs **10.6 s**,
and every spawned worker process paid it, despite the kernel having its
own hand-written PAV and never touching sklearn. On an 11-worker pool
that was ~117 s of pure startup per batch. Splitting this helper out
removes sklearn from the fast path entirely.
"""

import numpy as np


def capsule_node_band(n_nodes: int, n_pcm_nodes: int, anchor: str) -> np.ndarray:
    """The contiguous band of node indices holding capsules, placed around
    `anchor` ("bottom" / "center" / "top"). i=0 is the BOTTOM node."""
    n_pcm_nodes = max(1, min(n_nodes, n_pcm_nodes))
    if anchor == "bottom":
        start = 0
    elif anchor == "top":
        start = n_nodes - n_pcm_nodes
    else:  # "center" (default)
        start = (n_nodes - n_pcm_nodes) // 2
    return np.arange(start, start + n_pcm_nodes)
