"""
Status checks shown in the 'Setup status' sidebar.
"""
from __future__ import annotations

import os
from pathlib import Path

AUXDATA_DIR = Path(os.environ.get("DIR_POLYMER_AUXDATA", "/data/auxdata/static"))
ANCILLARY_DIR = Path(os.environ.get("DIR_POLYMER_ANCILLARY", "/data/ancillary"))
INPUT_DIR = Path("/data/input")
OUTPUT_DIR = Path("/data/output")

# Key file that must exist after "python -m polymer.get_auxdata".
AUXDATA_SENTINEL = AUXDATA_DIR / "generic" / "LUT.hdf"


def cython_modules_ok() -> bool:
    try:
        import polymer.polymer_main  # noqa: F401
        import polymer.water  # noqa: F401
        return True
    except Exception:
        return False


def auxdata_present() -> bool:
    return AUXDATA_SENTINEL.exists() and AUXDATA_SENTINEL.stat().st_size > 0


def auxdata_size_mb() -> float:
    if not AUXDATA_DIR.exists():
        return 0.0
    total = sum(f.stat().st_size for f in AUXDATA_DIR.rglob("*") if f.is_file())
    return total / (1024 * 1024)


def list_input_products() -> list[str]:
    """List candidate Level-1 products in /data/input (top-level files and folders)."""
    if not INPUT_DIR.exists():
        return []
    return sorted(p.name for p in INPUT_DIR.iterdir() if not p.name.startswith("."))


def overall_ready() -> bool:
    return cython_modules_ok() and auxdata_present()
