import stat

import pytest

import credentials as cred


@pytest.fixture
def cfgdir(tmp_path, monkeypatch):
    monkeypatch.setattr(cred, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cred, "NETRC", tmp_path / ".netrc")
    monkeypatch.setattr(cred, "CDSAPIRC", tmp_path / ".cdsapirc")
    return tmp_path


def test_earthdata_roundtrip_and_perms(cfgdir):
    cred.write_earthdata("alice", "s3cret")
    assert cred.read_earthdata() == {"login": "alice", "password": "s3cret"}
    mode = stat.S_IMODE((cfgdir / ".netrc").stat().st_mode)
    assert mode == 0o600
    cred.clear_earthdata()
    assert not (cfgdir / ".netrc").exists()
    assert cred.read_earthdata() == {}


def test_earthdata_preserves_other_machines(cfgdir):
    (cfgdir / ".netrc").write_text("machine example.com login x password y\n")
    cred.write_earthdata("alice", "pw")
    text = (cfgdir / ".netrc").read_text()
    assert "example.com" in text and "urs.earthdata.nasa.gov" in text


def test_cds_roundtrip(cfgdir):
    cred.write_cds("KEY123")
    assert cred.read_cds()["key"] == "KEY123"
    assert cred.read_cds()["url"].startswith("http")
    cred.clear_cds()
    assert cred.read_cds() == {}


def test_status_summary(cfgdir):
    assert cred.status() == {"earthdata": False, "earthdata_login": "", "cds": False}
    cred.write_earthdata("bob", "pw")
    cred.write_cds("k")
    s = cred.status()
    assert s["earthdata"] and s["cds"] and s["earthdata_login"] == "bob"
