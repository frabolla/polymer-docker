#!/usr/bin/env python
"""
Esecuzione di un singolo job Polymer, come sottoprocesso indipendente.

Uso:
    python polymer_job.py --config /percorso/job.json

Struttura di job.json:
{
    "input":   "/data/input/S3A_..._.SEN3",
    "sensor":  "auto" | "OLCI" | "MSI" | "MERIS" | "MODIS" | "VIIRS"
                     | "SeaWiFS" | "PRISMA" | "LANDSAT8" | "HICO",
    "output_dir": "/data/output",
    "output_name": "" ,          # opzionale: nome file esplicito
    "fmt":     "netcdf4" | "hdf4",
    "resolution": "60",          # solo MSI: "10" | "20" | "60"
    "ancillary": "auto" | "NASA" | "ERA5" | "none",
    "l1_kwargs":     {"sline": 0, "eline": -1, "scol": 0, "ecol": -1},
    "polymer_kwargs": {"multiprocessing": -1, "normalize": 0, ...}
}

Il sottoprocesso stampa il progresso su stdout (Polymer logga gia' le percentuali)
ed esce con codice 0 (successo) o 1 (errore, con traceback completo su stderr).
"""
from __future__ import annotations

import argparse
import json
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

    raise ValueError(f"Sensore non riconosciuto: {sensor!r}")


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
    # auto: usa NASA solo se il .netrc contiene le credenziali Earthdata
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())

    pk = dict(cfg.get("polymer_kwargs") or {})
    # OMP_NUM_THREADS: limita il multiprocessing di numpy quando Polymer gia' parallelizza
    mp = int(pk.get("multiprocessing", 0) or 0)
    os.environ.setdefault("OMP_NUM_THREADS", "1" if mp != 0 else str(os.cpu_count() or 1))

    print(f"[polymer_job] input   = {cfg['input']}", flush=True)
    print(f"[polymer_job] sensore = {cfg.get('sensor', 'auto')}", flush=True)
    print(f"[polymer_job] output  = {cfg.get('output_dir')}  ({cfg.get('fmt')})", flush=True)
    print(f"[polymer_job] kwargs  = {pk}", flush=True)

    from polymer.main import run_atm_corr

    l1 = build_level1(cfg)
    l2 = build_level2(cfg)
    result = run_atm_corr(l1, l2, **pk)

    out = getattr(result, "filename", None) or cfg.get("output_dir")
    print(f"[polymer_job] COMPLETATO -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
