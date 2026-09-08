"""
PNG preview of a Polymer Level-2 product.

- make_png(path, out)            -> auto: water-reflectance RGB, else logchl, else
                                   the first informative 2D variable
- make_png(path, out, var=NAME)  -> map of that variable + a value histogram
- list_2d_vars(path)             -> names that can be shown as a map

Polymer's Level-2 NetCDF (polymer/level2_nc.py) has exactly two dimensions,
`height` and `width`; every variable is 2D. Multi-band datasets are written as
one 2D variable per band, named `<dataset><wavelength>` (e.g. `Rw443`, `Rw560`).
Band centres are not always the exact nominal wavelengths (hyperspectral sensors
such as PRISMA), so band lookup here matches the nearest wavelength within a
tolerance rather than requiring an exact name.
"""
from __future__ import annotations

import re

import numpy as np

import i18n

# Nominal wavelengths (nm) used for the auto RGB composite.
_RGB = {"r": 665, "g": 560, "b": 443}
# Datasets that hold water-leaving reflectance, most-preferred first. `Rw` is
# Polymer's default output; `rho_w_` / `rho_w` cover alternative configurations.
_RW_PREFIXES = ("Rw", "rho_w_", "rho_w")
# Largest band-centre offset (nm) still accepted when matching by nearest wavelength.
_WL_TOLERANCE = 20

_SPATIAL_DIMS = {"height", "width", "y", "x", "rows", "columns", "line", "column"}
# Variables that are 2D but not informative as a standalone preview map.
_UNINTERESTING = {"latitude", "longitude", "lat", "lon"}
# `<prefix><integer>` where the integer is a 3-4 digit wavelength in nm.
_BANDNAME_RE = re.compile(r"^(.+?)(\d{3,4})$")


def _open(path: str):
    import xarray as xr

    try:
        return xr.open_dataset(path)
    except Exception:
        return xr.open_dataset(path, engine="netcdf4")


def _is_spatial_2d(da, ds) -> bool:
    """True when `da` is a 2D array over the product's spatial grid."""
    if da.ndim != 2:
        return False
    dims = set(da.dims)
    # Known spatial dim names, or a file whose only dimensions are these two.
    return dims <= _SPATIAL_DIMS or dims == set(ds.dims)


def list_2d_vars(path: str) -> list[str]:
    ds = _open(path)
    try:
        return sorted(
            str(v) for v in ds.data_vars if _is_spatial_2d(ds[v], ds)
        )
    finally:
        ds.close()


def _find_band_var(ds, prefixes, wl):
    """Water-reflectance band nearest to `wl` nm: exact name, then nearest match."""
    # 1) exact "<prefix><wl>" (fast path, e.g. Rw560)
    for pref in prefixes:
        name = f"{pref}{wl}"
        if name in ds.variables:
            return ds[name]

    # 2) nearest wavelength among "<prefix><integer>" variables
    best_name, best_delta = None, None
    for var in ds.variables:
        m = _BANDNAME_RE.match(str(var))
        if not m or m.group(1) not in prefixes:
            continue
        delta = abs(int(m.group(2)) - wl)
        if best_delta is None or delta < best_delta:
            best_name, best_delta = str(var), delta
    if best_name is not None and best_delta <= _WL_TOLERANCE:
        return ds[best_name]

    # 3) a single variable with a `bands` dimension (non-split layouts)
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


def _first_informative_2d(ds, level2_path: str):
    """A data variable worth showing as a map, preferring non-coordinate ones."""
    twod = list_2d_vars(level2_path)
    if not twod:
        return None
    for name in twod:
        if name.lower() not in _UNINTERESTING:
            return name
    return twod[0]


def make_png(level2_path: str, out_png: str, var: str | None = None) -> str:
    """Write `out_png`; return a short description of what it shows."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ds = _open(level2_path)
    try:
        if var and var in ds.variables:
            data = np.asarray(ds[var].values, dtype="float32")
            fig, (ax, axh) = plt.subplots(
                1, 2, figsize=(11, 5), gridspec_kw={"width_ratios": [3, 2]}
            )
            im = ax.imshow(data, origin="upper", cmap="viridis")
            fig.colorbar(im, ax=ax, shrink=0.8)
            ax.set_xticks([])
            ax.set_yticks([])
            finite = data[np.isfinite(data)]
            if finite.size:
                axh.hist(finite.ravel(), bins=80, color="#4C78A8")
            axh.set_title("histogram")
            desc = i18n.t("quicklook.map_var", name=var)
            ax.set_title(desc, fontsize=10)
            fig.tight_layout()
            fig.savefig(out_png, dpi=110)
            plt.close(fig)
            return desc

        r = _find_band_var(ds, _RW_PREFIXES, _RGB["r"])
        g = _find_band_var(ds, _RW_PREFIXES, _RGB["g"])
        b = _find_band_var(ds, _RW_PREFIXES, _RGB["b"])

        fig, ax = plt.subplots(figsize=(7, 7))
        if r is not None and g is not None and b is not None:
            rgb = np.dstack([_stretch(r.values), _stretch(g.values), _stretch(b.values)])
            ax.imshow(rgb, origin="upper")
            desc = i18n.t("quicklook.rgb")
        else:
            chl = None
            for cand in ("logchl", "logchl_mean", "logchl_stdev"):
                if cand in ds.variables:
                    chl = ds[cand]
                    break
            if chl is None:
                name = _first_informative_2d(ds, level2_path)
                if name is None:
                    raise RuntimeError("No 2D variable suitable for a preview.")
                chl = ds[name]
                desc = i18n.t("quicklook.map_var", name=name)
            else:
                desc = i18n.t("quicklook.map_chl", name=chl.name)
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
