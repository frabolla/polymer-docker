"""
Anteprima PNG di un prodotto Level-2 di Polymer.

Prova, in ordine:
  1. RGB dalla riflettanza dell'acqua (Rw/rho_w a ~665/560/443 nm)
  2. mappa di logchl / logchl_mean
  3. prima variabile 2D disponibile
"""
from __future__ import annotations

import numpy as np

_RGB = {"r": 665, "g": 560, "b": 443}


def _open(path: str):
    import xarray as xr

    try:
        return xr.open_dataset(path)
    except Exception:
        return xr.open_dataset(path, engine="netcdf4")


def _find_band_var(ds, prefixes, wl):
    for pref in prefixes:
        name = f"{pref}{wl}"
        if name in ds.variables:
            return ds[name]
    for pref in prefixes:
        if pref in ds.variables and "bands" in ds[pref].dims and "bands" in ds:
            bands = np.asarray(ds["bands"].values)
            idx = int(np.argmin(np.abs(bands - wl)))
            return ds[pref].isel(bands=idx)
    return None


def _stretch(a):
    a = np.asarray(a, dtype="float32")
    finite = a[np.isfinite(a)]
    if finite.size == 0:
        return np.zeros_like(a)
    lo, hi = np.percentile(finite, [2, 98])
    if hi <= lo:
        hi = lo + 1e-6
    return np.clip((a - lo) / (hi - lo), 0, 1)


def make_png(level2_path: str, out_png: str) -> str:
    """Genera `out_png` e restituisce una breve descrizione di cosa mostra."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ds = _open(level2_path)
    try:
        prefixes = ["rho_w_", "Rw", "rho_w"]
        r = _find_band_var(ds, prefixes, _RGB["r"])
        g = _find_band_var(ds, prefixes, _RGB["g"])
        b = _find_band_var(ds, prefixes, _RGB["b"])

        fig, ax = plt.subplots(figsize=(7, 7))
        if r is not None and g is not None and b is not None:
            rgb = np.dstack([_stretch(r.values), _stretch(g.values), _stretch(b.values)])
            ax.imshow(rgb, origin="upper")
            desc = "RGB della riflettanza dell'acqua (665 / 560 / 443 nm)"
        else:
            chl = None
            for cand in ("logchl", "logchl_mean", "logchl_stdev"):
                if cand in ds.variables:
                    chl = ds[cand]
                    break
            if chl is None:
                twod = [
                    v for v in ds.data_vars
                    if ds[v].ndim == 2 and set(ds[v].dims) <= {"height", "width", "y", "x"}
                ]
                if not twod:
                    raise RuntimeError("Nessuna variabile 2D adatta per l'anteprima.")
                chl = ds[twod[0]]
                desc = f"Mappa di '{twod[0]}'"
            else:
                desc = f"Mappa di '{chl.name}' (log clorofilla)"
            im = ax.imshow(chl.values, origin="upper", cmap="viridis")
            fig.colorbar(im, ax=ax, shrink=0.8)
        ax.set_title(desc, fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
        fig.tight_layout()
        fig.savefig(out_png, dpi=110)
        plt.close(fig)
        return desc
    finally:
        ds.close()
