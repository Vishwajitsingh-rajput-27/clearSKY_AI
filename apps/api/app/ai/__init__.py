"""Research AI package for clearSKY reconstruction.

Modules in this package are intentionally imported lazily by runtime services so the public
FastAPI app can continue to run in CPU/OpenCV-only deployments without trained weights.
"""

