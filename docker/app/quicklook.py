"""
PNG preview of a Polymer Level-2 product.

- make_png(path, out)            -> auto: water-reflectance RGB, else logchl, else
                                   the first 2D variable
- make_png(path, out, var=NAME)  -> map of that variable + a value histogram
- list_2d_vars(path)             -> names that can be shown as a map
"""
from __future__ import annotations

import numpy as np

import i18n

_RGB = {"r": 665, "g": 560, "b": 443}
_SPATIAL_DIMS = {"height", "width", "y", "x", "rows", "columns", "line", "column"}


def _open(path: str):
    import xarray as xr

    try:
        return xr.open_dataset(path)
    except Exception:
        return xr.open_dataset(path, engine="netcdf4")


def list_2d_vars(path: str) -> list[str]:
    ds = _open(path)
    try:
        out = []
        for v in ds.data_vars:
            da = ds[v]
            if da.ndim == 2 and set(da.dims) <= _SPATIAL_DIMS:
                out.append(str(v))
        return sorted(out)
    finally:
        ds.close()


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

        prefixes = ["rho_w_", "Rw", "rho_w"]
        r = _find_band_var(ds, prefixes, _RGB["r"])
        g = _find_band_var(ds, prefixes, _RGB["g"])
        b = _find_band_var(ds, prefixes, _RGB["b"])

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
                twod = list_2d_vars(level2_path)
                if not twod:
                    raise RuntimeError("No 2D variable suitable for a preview.")
                chl = ds[twod[0]]
                desc = i18n.t("quicklook.map_var", name=twod[0])
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
