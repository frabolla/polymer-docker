#!/usr/bin/env python
"""
Run a single Polymer job as an independent subprocess.

Usage:
    python polymer_job.py --config /path/to/job.json [--run-id ID] [--result PATH]

Structure of job.json:
{
    "input":   "/data/input/S3A_..._.SEN3",
    "sensor":  "auto" | "OLCI" | "MSI" | "MERIS" | "MODIS" | "VIIRS"
                     | "SeaWiFS" | "PRISMA" | "LANDSAT8" | "HICO",
    "output_dir": "/data/output",
    "output_name": "" ,          # optional: explicit file name
    "fmt":     "netcdf4" | "hdf4",
    "resolution": "60",          # MSI only: "10" | "20" | "60"
    "ancillary": "auto" | "NASA" | "ERA5" | "none",
    "l1_kwargs":     {"sline": 0, "eline": -1, "scol": 0, "ecol": -1},
    "polymer_kwargs": {"multiprocessing": -1, "normalize": 0, ...}
}

The subprocess prints progress to stdout:
  [polymer_job] BLOCKS_TOTAL <n|unknown>   once, near the start
  Processing block: ...                     one line per block (from Polymer)
  [polymer_job] COMPLETED -> <path>         on success
It exits 0 on success, 1 on error (full traceback on stderr). If --result is
given, a small JSON summary is written there on exit.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import traceback
from pathlib import Path


def resolve_sensor(cfg: dict) -> str:
    """Sensor to use: the explicit choice, or a name-based guess for 'auto'."""
    sensor = (cfg.get("sensor") or "auto").lower()
    if sensor in ("", "auto"):
        name = Path(cfg["input"]).name
        if name.startswith("PRS_L1_STD_OFFL_"):
            return "prisma"
        if name.startswith(("PRS_L2C", "PRS_L2D")):
            return "prisma"
    return sensor


# Readers whose constructor accepts `landmask=` (Level1_NASA / the generic
# Level1 dispatcher do not).
_LANDMASK_SENSORS = {"olci", "msi", "meris", "prisma", "hico", "landsat8"}
# Where GSW tiles live if the user picked the "gsw" land mask.
GSW_DIR = Path(os.environ.get("DIR_DATA", "/data")) / "auxdata" / "gsw"
_KEEP = object()  # sentinel: leave the reader's own landmask default alone


def _land_mode(cfg: dict) -> str:
    m = (cfg.get("landmask") or "mask").lower()
    return {"default": "mask", "none": "process", "no": "process", "off": "process"}.get(m, m)


def _resolve_landmask(cfg: dict):
    """Turn the UI's land-handling choice into what a Level1 reader expects."""
    mode = _land_mode(cfg)
    if mode == "mask":
        return _KEEP
    if mode == "process":
        return None  # drop any geographic land mask
    if mode == "gsw":
        from polymer.gsw import GSW

        return GSW(directory=str(GSW_DIR))
    return _KEEP


def apply_land_mode(cfg: dict, pk: dict) -> None:
    """
    'process' land handling also needs BITMASK_INVALID without the LAND bit, or
    Polymer still skips land pixels flagged by the reader (PRISMA reads them from
    the product's own LandCover_Mask regardless of the geographic mask). A value
    the user typed in Advanced parameters wins.
    """
    if _land_mode(cfg) == "process":
        from params_schema import BITMASK_INVALID_PROCESS_LAND

        pk.setdefault("BITMASK_INVALID", BITMASK_INVALID_PROCESS_LAND)


def build_level1(cfg: dict):
    from polymer.level1 import Level1

    src = cfg["input"]
    sensor = resolve_sensor(cfg)
    l1_kwargs = dict(cfg.get("l1_kwargs") or {})

    anc = build_ancillary(cfg.get("ancillary", "auto"))
    if anc is not None:
        l1_kwargs["ancillary"] = anc

    if sensor in _LANDMASK_SENSORS:
        lm = _resolve_landmask(cfg)
        if lm is not _KEEP:
            l1_kwargs["landmask"] = lm

    if sensor in ("", "auto"):
        return Level1(src, **l1_kwargs)

    if sensor == "olci":
        from polymer.level1_olci import Level1_OLCI
        return Level1_OLCI(src, **l1_kwargs)
    if sensor == "msi":
        from polymer.level1_msi import Level1_MSI
        res = str(cfg.get("resolution") or "60")
        return Level1_MSI(src, resolution=res, **l1_kwargs)
    if sensor == "meris":
        from polymer.level1_meris import Level1_MERIS
        return Level1_MERIS(src, **l1_kwargs)
    if sensor in ("modis", "viirs", "seawifs"):
        from polymer.level1_nasa import Level1_MODIS, Level1_SeaWiFS, Level1_VIIRS
        cls = {"modis": Level1_MODIS, "viirs": Level1_VIIRS, "seawifs": Level1_SeaWiFS}[sensor]
        return cls(src, **l1_kwargs)
    if sensor == "prisma":
        from polymer.level1_prisma import Level1_PRISMA
        return Level1_PRISMA(src, **l1_kwargs)
    if sensor == "landsat8":
        from polymer.level1_landsat8 import Level1_OLI
        return Level1_OLI(src, **l1_kwargs)
    if sensor == "hico":
        from polymer.level1_hico import Level1_HICO
        return Level1_HICO(src, **l1_kwargs)

    raise ValueError(f"Unknown sensor: {sensor!r}")


def _auto_ancillary_kind() -> str | None:
    """
    Which ancillary source 'auto' means, from the files the Setup tab writes.

    Never assumes NASA: a NASA Earthdata `.netrc` wins, then a Copernicus
    `.cdsapirc` (ERA5). Nothing configured -> None (no meteo download attempted).
    """
    home = Path(os.environ.get("HOME", "/data/config"))
    netrc = home / ".netrc"
    if netrc.exists() and "urs.earthdata.nasa.gov" in netrc.read_text():
        return "nasa"
    if (home / ".cdsapirc").exists():
        return "era5"
    return None


def build_ancillary(kind: str):
    kind = (kind or "auto").lower()
    if kind == "auto":
        kind = _auto_ancillary_kind() or "none"
    if kind == "none":
        return None
    if kind == "era5":
        from polymer.ancillary_era5 import Ancillary_ERA5
        return Ancillary_ERA5()
    if kind == "nasa":
        from polymer.ancillary import Ancillary_NASA
        return Ancillary_NASA()
    raise ValueError(f"Unknown ancillary source: {kind!r}")


def build_level2(cfg: dict):
    from polymer.level2 import Level2

    fmt = cfg.get("fmt", "netcdf4")
    out_dir = cfg.get("output_dir") or "/data/output"
    name = (cfg.get("output_name") or "").strip()
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    if name:
        filename = str(Path(out_dir) / name)
        return Level2(filename=filename, fmt=fmt, overwrite=True)
    ext = ".polymer.nc" if fmt == "netcdf4" else ".polymer.hdf"
    return Level2(fmt=fmt, outdir=out_dir, ext=ext, overwrite=True)


def estimate_total_blocks(cfg: dict) -> int | None:
    """Best-effort: open the Level-1 once to read its shape and block size."""
    # PRISMA's reader downloads ancillary data in __init__ and has no context
    # manager, so probing it would do that expensive work twice. Skip it.
    if resolve_sensor(cfg) == "prisma":
        return None
    try:
        with build_level1(cfg) as probe:
            bs = getattr(probe, "blocksize", 100)
            bsy, bsx = bs if isinstance(bs, (tuple, list)) else (bs, bs)
            h = int(getattr(probe, "height"))
            w = int(getattr(probe, "width"))
            return math.ceil(h / bsy) * math.ceil(w / bsx)
    except Exception as exc:  # never fatal — progress is a nice-to-have
        print(f"[polymer_job] block estimate skipped ({exc})", flush=True)
        return None


def _write_result(path: str, run_id: str, rc: int, output: str | None, error: str) -> None:
    if not path:
        return
    try:
        p = Path(path)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(
            json.dumps(
                {"run_id": run_id, "rc": rc, "output": output, "error": error},
                ensure_ascii=False,
            )
        )
        tmp.replace(p)  # atomic
    except Exception:
        pass


def _has_meteo_credentials() -> bool:
    home = Path(os.environ.get("HOME", "/data/config"))
    netrc = home / ".netrc"
    if netrc.exists() and "urs.earthdata.nasa.gov" in netrc.read_text():
        return True
    return (home / ".cdsapirc").exists()


def _preflight(cfg: dict) -> str | None:
    """Cheap input checks before doing any real work. Returns an error string or None."""
    src = Path(cfg["input"])
    if not src.exists():
        return f"Input file not found: {src.name} (in data/input/)."

    sensor = resolve_sensor(cfg)

    if sensor == "prisma":
        if src.name.startswith("PRS_L1_STD_OFFL_"):
            companion = src.with_name(
                src.name.replace("PRS_L1_STD_OFFL_", "PRS_L2C_STD_", 1)
            )
            if not companion.exists():
                return (
                    "PRISMA needs both files: the L1 and its L2C companion "
                    f"'{companion.name}' in the same folder (this one is missing)."
                )
        if not _has_meteo_credentials():
            return (
                "PRISMA needs meteorological data (ozone / wind / pressure) that "
                "Polymer downloads from NASA Earthdata. Add a NASA Earthdata "
                "account (or a Copernicus CDS key) in the Setup tab, then run again."
            )

    if (cfg.get("landmask") or "").lower() == "gsw":
        if sensor not in _LANDMASK_SENSORS:
            return (
                f"The '{sensor}' reader does not support a land mask. Pick "
                "'Product's built-in mask' or 'None' for the land mask."
            )
        if not GSW_DIR.is_dir() or not any(GSW_DIR.iterdir()):
            return (
                "The Global Surface Water land mask needs its dataset, which is "
                f"not present ({GSW_DIR}). Put the GSW tiles there, or choose a "
                "different land mask."
            )
    return None


_ERROR_HINTS = [
    (
        ("authenticating to NASA EarthData", "urs.earthdata", "401 Unauthorized",
         "Username/Password Authentication Failed"),
        "The NASA Earthdata login failed or is missing. Open the Setup tab and "
        "enter (or correct) your Earthdata username and password, then run again.",
    ),
    (
        ("does not exist.Please create it for hosting ERA5", "ancillary/ERA5\" does not"),
        "The ERA5 data folder is missing inside the container. Rebuild the image "
        "(docker compose build) — newer images create it automatically at startup.",
    ),
    (
        ("licence", "not agreed to the required terms", "required licences",
         "Terms and conditions have not been accepted"),
        "Your Copernicus account has not accepted the ERA5 licence yet. Sign in at "
        "cds.climate.copernicus.eu, open the 'ERA5 hourly data on single levels' "
        "dataset, accept its terms at the bottom of the page, then run again.",
    ),
    (
        ("401 Client Error", "Authorization failed", "invalid_token",
         "Bad token", "403 Client Error"),
        "The Copernicus CDS key was not accepted. Re-copy it from your CDS "
        "profile page into the Setup tab, then run again.",
    ),
    (
        # downstream symptom when the meteo/ozone download failed
        ("polymer/ancillary.py", "polymer/ancillary_era5.py"),
        "The meteorological data (ozone / wind / pressure) could not be "
        "downloaded. Check your NASA Earthdata account or Copernicus CDS key "
        "in the Setup tab — it is missing, wrong, or the service is unreachable.",
    ),
    (
        ("Unable to detect sensor",),
        "Polymer could not tell which sensor this file is from. Pick the sensor "
        "explicitly in the Processing tab instead of leaving it on 'auto'.",
    ),
    (
        ("LUT.hdf", "No such file or directory: '/data/auxdata", "get_auxdata"),
        "The auxiliary data is missing or incomplete. Use 'Download / update "
        "auxiliary data' on the Setup tab, then run again.",
    ),
    (
        ("/data/ancillary", "METEO does not exist"),
        "The ancillary-data folder is missing inside the container. Rebuild the "
        "image (docker compose build) so the latest fix is applied.",
    ),
    (
        ("wget: not found", "wget: command not found"),
        "'wget' is missing from the image. Rebuild it (docker compose build) so "
        "the latest fix is applied.",
    ),
    (
        ("MemoryError", "Cannot allocate memory", "Killed"),
        "The container ran out of memory. In Docker Desktop → Settings → "
        "Resources, raise the memory limit (8 GB or more), then run again.",
    ),
]


def _humanize_error(text: str) -> str:
    """Turn a raw traceback / message into one plain-language sentence for the user."""
    low = text
    for needles, message in _ERROR_HINTS:
        if any(n in low for n in needles):
            return message
    last = text.strip().splitlines()[-1] if text.strip() else "unknown error"
    return f"Processing failed: {last}"


def run(args) -> int:
    cfg = json.loads(Path(args.config).read_text())

    pk = dict(cfg.get("polymer_kwargs") or {})
    apply_land_mode(cfg, pk)
    mp = int(pk.get("multiprocessing", 0) or 0)
    os.environ.setdefault("OMP_NUM_THREADS", "1" if mp != 0 else str(os.cpu_count() or 1))

    resolved = resolve_sensor(cfg)
    print(f"[polymer_job] run-id  = {args.run_id or '-'}", flush=True)
    print(f"[polymer_job] input   = {cfg['input']}", flush=True)
    print(
        f"[polymer_job] sensor  = {cfg.get('sensor', 'auto')}"
        + (f" -> {resolved}" if resolved != (cfg.get('sensor') or 'auto').lower() else ""),
        flush=True,
    )
    print(f"[polymer_job] output  = {cfg.get('output_dir')}  ({cfg.get('fmt')})", flush=True)
    print(f"[polymer_job] kwargs  = {pk}", flush=True)

    err = _preflight(cfg)
    if err:
        print(f"[polymer_job] ERROR: {err}", flush=True)
        _write_result(args.result, args.run_id, 1, None, err)
        return 1

    total = estimate_total_blocks(cfg)
    print(f"[polymer_job] BLOCKS_TOTAL {total if total else 'unknown'}", flush=True)

    from polymer.main import run_atm_corr

    try:
        l1 = build_level1(cfg)
        l2 = build_level2(cfg)
        result = run_atm_corr(l1, l2, **pk)
    except Exception:
        tb = traceback.format_exc()
        traceback.print_exc()  # full detail stays in the job log
        friendly = _humanize_error(tb)
        print(f"[polymer_job] ERROR: {friendly}", flush=True)
        _write_result(args.result, args.run_id, 1, None, friendly)
        return 1

    out = getattr(result, "filename", None) or cfg.get("output_dir")
    print(f"[polymer_job] COMPLETED -> {out}", flush=True)
    _write_result(args.result, args.run_id, 0, str(out), "")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--run-id", default="", dest="run_id")
    ap.add_argument("--result", default="")
    _a = ap.parse_args()
    try:
        sys.exit(run(_a))
    except SystemExit:
        raise
    except Exception:
        tb = traceback.format_exc()
        traceback.print_exc()
        _write_result(_a.result, _a.run_id, 1, None, _humanize_error(tb))
        sys.exit(1)
