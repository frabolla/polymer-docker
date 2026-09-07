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


def build_level1(cfg: dict):
    from polymer.level1 import Level1

    src = cfg["input"]
    sensor = (cfg.get("sensor") or "auto").lower()
    l1_kwargs = dict(cfg.get("l1_kwargs") or {})

    anc = build_ancillary(cfg.get("ancillary", "auto"))
    if anc is not None:
        l1_kwargs["ancillary"] = anc

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


def build_ancillary(kind: str):
    kind = (kind or "auto").lower()
    if kind == "none":
        return None
    if kind == "era5":
        from polymer.ancillary_era5 import Ancillary_ERA5
        return Ancillary_ERA5()
    if kind == "nasa":
        from polymer.ancillary import Ancillary_NASA
        return Ancillary_NASA()
    # auto: use NASA only if the .netrc contains Earthdata credentials
    netrc = Path(os.environ.get("HOME", "/data/config")) / ".netrc"
    if netrc.exists() and "urs.earthdata.nasa.gov" in netrc.read_text():
        from polymer.ancillary import Ancillary_NASA
        return Ancillary_NASA()
    return None


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


def run(args) -> int:
    cfg = json.loads(Path(args.config).read_text())

    pk = dict(cfg.get("polymer_kwargs") or {})
    mp = int(pk.get("multiprocessing", 0) or 0)
    os.environ.setdefault("OMP_NUM_THREADS", "1" if mp != 0 else str(os.cpu_count() or 1))

    print(f"[polymer_job] run-id  = {args.run_id or '-'}", flush=True)
    print(f"[polymer_job] input   = {cfg['input']}", flush=True)
    print(f"[polymer_job] sensor  = {cfg.get('sensor', 'auto')}", flush=True)
    print(f"[polymer_job] output  = {cfg.get('output_dir')}  ({cfg.get('fmt')})", flush=True)
    print(f"[polymer_job] kwargs  = {pk}", flush=True)

    total = estimate_total_blocks(cfg)
    print(f"[polymer_job] BLOCKS_TOTAL {total if total else 'unknown'}", flush=True)

    from polymer.main import run_atm_corr

    l1 = build_level1(cfg)
    l2 = build_level2(cfg)
    result = run_atm_corr(l1, l2, **pk)

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
        last = tb.strip().splitlines()[-1] if tb.strip() else "error"
        _write_result(_a.result, _a.run_id, 1, None, last)
        sys.exit(1)
