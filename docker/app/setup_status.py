"""
Status checks shown in the 'Setup status' sidebar, plus auxiliary-data
integrity verification.
"""
from __future__ import annotations

import os
import shutil
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
        if p.name.startswith("PRS_L2C_STD_"):
            continue  # PRISMA L2C is a companion of the L1, not a product to pick
        out.append(p.name)
        granule = p / "GRANULE"
        if granule.is_dir():
            for g in sorted(granule.iterdir()):
                if g.is_dir():
                    out.append(f"{p.name}/GRANULE/{g.name}")
    return out


def overall_ready() -> bool:
    return cython_modules_ok() and auxdata_present()


def free_space_mb(path: str | Path = "/data") -> float:
    """Free space on the filesystem holding `path`, in MB (0 on error)."""
    try:
        return shutil.disk_usage(str(path)).free / (1024 * 1024)
    except Exception:
        return 0.0


# PRISMA needs BOTH files: the L1 the user selects AND the matching L2C product
# in the same folder (polymer/level1_prisma.py reads geometry from the L2C).
_PRISMA_L1_PREFIX = "PRS_L1_STD_OFFL_"
_PRISMA_L2C_PREFIX = "PRS_L2C_STD_"


def prisma_l2c_name(l1_name: str) -> str | None:
    """Expected PRISMA L2C companion file name for an L1 name (None if not a PRISMA L1)."""
    base = Path(l1_name).name
    if not base.startswith(_PRISMA_L1_PREFIX):
        return None
    return base.replace(_PRISMA_L1_PREFIX, _PRISMA_L2C_PREFIX, 1)


def missing_prisma_companion(l1_path: str | Path) -> str | None:
    """The L2C companion file name if PRISMA requires it and it is absent, else None."""
    p = Path(l1_path)
    comp = prisma_l2c_name(p.name)
    if comp is None:
        return None
    return None if (p.parent / comp).exists() else comp


# ------------------------------------------------------------ working folders
# The container's /data/input and /data/output are Docker bind mounts, so where
# they live on the host is decided *before* the container starts. The interface
# writes the user's choice to config/dirs.env; the launcher passes it to
# `docker compose --env-file` on the next start.
CONFIG_DIR = Path(os.environ.get("HOME", "/data/config"))
WORKDIRS_FILE = CONFIG_DIR / "dirs.env"
_WORKDIR_KEYS = {"input": "POLYMER_INPUT_DIR", "output": "POLYMER_OUTPUT_DIR"}


def _host_base() -> str:
    return os.environ.get("POLYMER_HOST_DIR", "").strip()


def default_workdirs() -> dict[str, str]:
    base = _host_base()
    return {name: (f"{base}/{name}" if base else "") for name in ("input", "output", "config")}


def load_workdirs() -> dict:
    """Effective host paths for input/output/config, plus whether they are custom."""
    dirs = default_workdirs()
    custom = False
    try:
        for line in WORKDIRS_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            for name, env in _WORKDIR_KEYS.items():
                if k.strip() == env and v.strip():
                    dirs[name] = v.strip()
                    custom = True
    except FileNotFoundError:
        pass
    except Exception:
        pass
    dirs["custom"] = custom
    return dirs


def save_workdirs(input_dir: str, output_dir: str) -> None:
    """Persist an input/output override for the next container start."""
    lines = ["# Written by the Polymer interface. Delete to restore the defaults."]
    for value, env in ((input_dir, "POLYMER_INPUT_DIR"), (output_dir, "POLYMER_OUTPUT_DIR")):
        value = (value or "").strip()
        if value:
            lines.append(f"{env}={value}")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    WORKDIRS_FILE.write_text("\n".join(lines) + "\n")


def clear_workdirs() -> None:
    WORKDIRS_FILE.unlink(missing_ok=True)


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
