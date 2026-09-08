"""Pure-Python helpers in polymer_job (no Polymer import needed)."""
import polymer_job as pj


def _cfg(name, sensor="auto"):
    return {"input": f"/data/input/{name}", "sensor": sensor}


def test_resolve_sensor_autocorrects_prisma():
    assert pj.resolve_sensor(_cfg("PRS_L1_STD_OFFL_x.he5")) == "prisma"
    assert pj.resolve_sensor(_cfg("PRS_L2C_STD_x.he5")) == "prisma"
    assert pj.resolve_sensor(_cfg("S3A_OL_1_EFR.SEN3")) == "auto"
    assert pj.resolve_sensor(_cfg("whatever.nc", sensor="OLCI")) == "olci"


def test_preflight_missing_input(tmp_path):
    err = pj._preflight({"input": str(tmp_path / "nope.he5"), "sensor": "OLCI"})
    assert err and "not found" in err


def test_preflight_prisma_missing_l2c(tmp_path, monkeypatch):
    monkeypatch.setattr(pj, "_has_meteo_credentials", lambda: True)
    l1 = tmp_path / "PRS_L1_STD_OFFL_20210101_20210101_0001.he5"
    l1.write_bytes(b"x")
    err = pj._preflight({"input": str(l1), "sensor": "auto"})
    assert err and "L2C companion" in err

    (tmp_path / "PRS_L2C_STD_20210101_20210101_0001.he5").write_bytes(b"x")
    assert pj._preflight({"input": str(l1), "sensor": "auto"}) is None


def test_preflight_prisma_needs_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(pj, "_has_meteo_credentials", lambda: False)
    l1 = tmp_path / "PRS_L1_STD_OFFL_a_b_0001.he5"
    l1.write_bytes(b"x")
    (tmp_path / "PRS_L2C_STD_a_b_0001.he5").write_bytes(b"x")
    err = pj._preflight({"input": str(l1), "sensor": "PRISMA"})
    assert err and ("Earthdata" in err or "CDS" in err)


def test_resolve_landmask_modes(monkeypatch):
    assert pj._resolve_landmask({}) is pj._KEEP
    assert pj._resolve_landmask({"landmask": "default"}) is pj._KEEP
    assert pj._resolve_landmask({"landmask": "none"}) is None
    assert pj._resolve_landmask({"landmask": "NONE"}) is None


def test_preflight_gsw_needs_dataset(tmp_path, monkeypatch):
    l1 = tmp_path / "scene.he5"
    l1.write_bytes(b"x")
    monkeypatch.setattr(pj, "GSW_DIR", tmp_path / "gsw")  # missing

    err = pj._preflight({"input": str(l1), "sensor": "MSI", "landmask": "gsw"})
    assert err and "Global Surface Water" in err

    (tmp_path / "gsw").mkdir()
    err = pj._preflight({"input": str(l1), "sensor": "MSI", "landmask": "gsw"})
    assert err and "Global Surface Water" in err  # dir exists but empty

    (tmp_path / "gsw" / "tile.nc").write_bytes(b"x")
    assert pj._preflight({"input": str(l1), "sensor": "MSI", "landmask": "gsw"}) is None


def test_preflight_gsw_rejected_for_unsupported_sensor(tmp_path):
    l1 = tmp_path / "A2004181.L1C"
    l1.write_bytes(b"x")
    err = pj._preflight({"input": str(l1), "sensor": "MODIS", "landmask": "gsw"})
    assert err and "does not support a land mask" in err


def test_humanize_error_known_cases():
    assert "Earthdata login failed" in pj._humanize_error(
        "wget ... Username/Password Authentication Failed"
    )
    assert "meteorological data" in pj._humanize_error(
        'File "/opt/polymer/polymer/ancillary.py", line 333\nTypeError: ... has no len()'
    )
    assert "sensor" in pj._humanize_error("Exception: Unable to detect sensor for file X")
    assert "auxiliary data" in pj._humanize_error(
        "FileNotFoundError: [Errno 2] No such file or directory: '/data/auxdata/static/generic/LUT.hdf'"
    )
    assert "out of memory" in pj._humanize_error("MemoryError")
    # unknown -> echoes the last line
    assert "boom" in pj._humanize_error("Traceback...\nRuntimeError: boom")


def test_humanize_error_era5_cases():
    assert "ERA5 data folder" in pj._humanize_error(
        'File ".../polymer/ancillary_era5.py", line 125\n'
        'Exception: Directory "/data/ancillary/ERA5" does not exist.'
        'Please create it for hosting ERA5 files.'
    )
    assert "licence" in pj._humanize_error(
        "ancillary_era5.py ...\nException: required licences not accepted: Terms "
        "and conditions have not been accepted"
    ).lower()
    assert "CDS key" in pj._humanize_error(
        "ancillary_era5.py ...\nHTTPError: 401 Client Error: Unauthorized"
    )


def test_auto_ancillary_kind(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert pj._auto_ancillary_kind() is None
    (tmp_path / ".cdsapirc").write_text("url: https://cds/api\nkey: abc\n")
    assert pj._auto_ancillary_kind() == "era5"
    (tmp_path / ".netrc").write_text(
        "machine urs.earthdata.nasa.gov login a password b\n"
    )
    assert pj._auto_ancillary_kind() == "nasa"  # Earthdata wins when both exist


def test_build_ancillary_none_and_unknown():
    assert pj.build_ancillary("none") is None
    try:
        pj.build_ancillary("bogus")
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected ValueError for an unknown source")
