"""
Status checks shown in the 'Setup status' sidebar, plus auxiliary-data
integrity verification.
"""
from __future__ import annotations

import os
from pathlib import Path

AUXDATA_DIR = Path(os.environ.get("DIR_POLYMER_AUXDATA", "/data/auxdata/static"))
ANCILLARY_DIR = Path(os.environ.get("DIR_POLYMER_ANCILLARY", "/data/ancillary"))
INPUT_DIR = Path("/data/input")
OUTPUT_DIR = Path("/data/output")

# Files "python -m polymer.get_auxdata" must have produced, with a rough minimum
# size in bytes for the ones large enough that a truncated download is obvious.
# (The full manifest is in polymer/get_auxdata.py.)
AUXDATA_REQUIRED: list[tuple[str, int]] = [
    ("generic/LUT.hdf", 5_000_000),
    ("common/no2_climatology.hdf", 100_000),
    ("common/trop_f_no2_200m.hdf", 10_000),
    ("common/morel_fq.dat", 10_000),
    ("common/AboveRrs_gCoef_w0.dat", 1_000),
    ("common/pope97.dat", 500),
    ("common/k_oz.csv", 200),
]

AUXDATA_SENTINEL = AUXDATA_DIR / "generic" / "LUT.hdf"


def cython_modules_ok() -> bool:
    try:
        import polymer.polymer_main  # noqa: F401
        import polymer.water  # noqa: F401
        return True
    except Exception:
        return False


def verify_auxdata() -> tuple[bool, list[str]]:
    """
    Check the required auxiliary files exist and are not obviously truncated.

    Returns (ok, problems). `problems` lists human-readable issues; empty when ok.
    """
    problems: list[str] = []
    for rel, min_size in AUXDATA_REQUIRED:
        p = AUXDATA_DIR / rel
        if not p.exists():
            problems.append(f"missing: {rel}")
        elif p.stat().st_size < min_size:
            problems.append(
                f"too small: {rel} ({p.stat().st_size} B < {min_size} B) — "
                "download likely incomplete"
            )
    return (not problems), problems


def auxdata_present() -> bool:
    return verify_auxdata()[0]


def auxdata_size_mb() -> float:
    if not AUXDATA_DIR.exists():
        return 0.0
    total = sum(f.stat().st_size for f in AUXDATA_DIR.rglob("*") if f.is_file())
    return total / (1024 * 1024)


def list_input_products() -> list[str]:
    """
    List candidate Level-1 products in /data/input.

    Top-level files and folders, plus one level of `*/GRANULE/*` (Sentinel-2
    products are often given as the granule directory inside a `.SAFE` folder).
    """
    if not INPUT_DIR.exists():
        return []
    out: list[str] = []
    for p in sorted(INPUT_DIR.iterdir()):
        if p.name.startswith("."):
            continue
        out.append(p.name)
        granule = p / "GRANULE"
        if granule.is_dir():
            for g in sorted(granule.iterdir()):
                if g.is_dir():
                    out.append(f"{p.name}/GRANULE/{g.name}")
    return out


def overall_ready() -> bool:
    return cython_modules_ok() and auxdata_present()


def app_version() -> str:
    """Version string: env var, then /app/VERSION, then 'dev'."""
    v = os.environ.get("POLYMER_GUI_VERSION", "").strip()
    if v and v != "dev":
        return v
    try:
        f = Path(__file__).parent / "VERSION"
        t = f.read_text().strip()
        if t:
            return t
    except Exception:
        pass
    return v or "dev"
