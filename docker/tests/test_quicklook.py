"""quicklook against a synthetic Polymer-shaped Level-2 NetCDF.

Skipped where xarray / netCDF4 are absent (e.g. the lean CI 'test' job); runs in
the container image, which has the full scientific stack.
"""
import numpy as np
import pytest

xr = pytest.importorskip("xarray")
pytest.importorskip("netCDF4")

import quicklook


def _write_l2(path, band_names=("Rw443", "Rw560", "Rw665"), extra=None):
    """A Level-2-like file: 2D vars over ('height', 'width'), like level2_nc.py."""
    h, w = 12, 10
    rng = np.random.default_rng(0)
    data = {name: (("height", "width"), rng.random((h, w), dtype="float32"))
            for name in band_names}
    data["logchl"] = (("height", "width"), rng.random((h, w), dtype="float32"))
    data["latitude"] = (("height", "width"), rng.random((h, w), dtype="float32"))
    data["longitude"] = (("height", "width"), rng.random((h, w), dtype="float32"))
    for k, v in (extra or {}).items():
        data[k] = (("height", "width"), v)
    xr.Dataset(data).to_netcdf(path)
    return str(path)


def test_list_2d_vars_finds_maps(tmp_path):
    p = _write_l2(tmp_path / "out.nc")
    got = quicklook.list_2d_vars(p)
    assert {"Rw443", "Rw560", "Rw665", "logchl", "latitude", "longitude"} <= set(got)


def test_make_png_auto_uses_rgb(tmp_path):
    p = _write_l2(tmp_path / "out.nc")
    out = tmp_path / "prev.png"
    desc = quicklook.make_png(p, str(out))
    assert out.exists() and out.stat().st_size > 0
    assert desc == quicklook.i18n.t("quicklook.rgb")


def test_rgb_matches_nearest_wavelength(tmp_path):
    # Band centres offset from the nominal 443/560/665 (hyperspectral-style).
    p = _write_l2(tmp_path / "out.nc", band_names=("Rw444", "Rw558", "Rw667"))
    out = tmp_path / "prev.png"
    desc = quicklook.make_png(p, str(out))
    assert desc == quicklook.i18n.t("quicklook.rgb")


def test_falls_back_to_logchl_when_no_bands(tmp_path):
    p = _write_l2(tmp_path / "out.nc", band_names=())
    out = tmp_path / "prev.png"
    desc = quicklook.make_png(p, str(out))
    assert out.exists()
    assert "logchl" in desc or desc == quicklook.i18n.t("quicklook.map_chl", name="logchl")


def test_first_informative_2d_skips_coordinates(tmp_path):
    p = tmp_path / "coords_plus_one.nc"
    h, w = 5, 5
    xr.Dataset(
        {
            "latitude": (("height", "width"), np.zeros((h, w), "float32")),
            "longitude": (("height", "width"), np.zeros((h, w), "float32")),
            "bitmask": (("height", "width"), np.ones((h, w), "float32")),
        }
    ).to_netcdf(p)
    ds = quicklook._open(str(p))
    try:
        # 'bitmask' is picked ahead of the latitude/longitude coordinate ramps
        assert quicklook._first_informative_2d(ds, str(p)) == "bitmask"
    finally:
        ds.close()


def test_make_png_specific_var(tmp_path):
    p = _write_l2(tmp_path / "out.nc")
    out = tmp_path / "prev.png"
    desc = quicklook.make_png(p, str(out), var="logchl")
    assert out.exists() and out.stat().st_size > 0
    assert "logchl" in desc
