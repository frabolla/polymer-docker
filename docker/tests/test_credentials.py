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


@pytest.mark.parametrize("pw", ["my pass#1", 'q"uo\\te', "back\\slash end"])
def test_earthdata_special_chars_roundtrip(cfgdir, pw):
    import netrc

    cred.write_earthdata("alice", pw)
    assert cred.read_earthdata() == {"login": "alice", "password": pw}
    # Python's own parser (used by requests) must agree.
    entry = netrc.netrc(str(cfgdir / ".netrc")).authenticators(cred.EARTHDATA_MACHINE)
    assert entry[0] == "alice" and entry[2] == pw


def test_line_breaks_are_rejected(cfgdir):
    with pytest.raises(ValueError):
        cred.write_earthdata("alice", "pw\nmachine evil.example login x password y")
    with pytest.raises(ValueError):
        cred.write_cds("KEY\nurl: https://evil.example")
    assert not (cfgdir / ".netrc").exists() and not (cfgdir / ".cdsapirc").exists()


def test_cds_file_is_private(cfgdir):
    cred.write_cds("KEY123")
    assert stat.S_IMODE((cfgdir / ".cdsapirc").stat().st_mode) == 0o600
