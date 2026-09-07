import pytest

import setup_status as status


@pytest.fixture
def aux(tmp_path, monkeypatch):
    monkeypatch.setattr(status, "AUXDATA_DIR", tmp_path)
    monkeypatch.setattr(status, "AUXDATA_SENTINEL", tmp_path / "generic" / "LUT.hdf")
    for rel, min_size in status.AUXDATA_REQUIRED:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"0" * (min_size + 10))
    return tmp_path


def test_verify_ok_when_all_present(aux):
    ok, problems = status.verify_auxdata()
    assert ok and problems == []
    assert status.auxdata_present()


def test_verify_reports_missing(aux):
    (aux / "common" / "pope97.dat").unlink()
    ok, problems = status.verify_auxdata()
    assert not ok
    assert any("missing" in p and "pope97.dat" in p for p in problems)


def test_verify_reports_truncated(aux):
    (aux / "generic" / "LUT.hdf").write_bytes(b"tiny")
    ok, problems = status.verify_auxdata()
    assert not ok
    assert any("too small" in p for p in problems)


def test_free_space_positive(tmp_path):
    assert status.free_space_mb(tmp_path) > 0


def test_list_input_products_includes_granules(tmp_path, monkeypatch):
    monkeypatch.setattr(status, "INPUT_DIR", tmp_path)
    (tmp_path / "S3A_OL_1.SEN3").mkdir()
    (tmp_path / "scene.nc").write_text("x")
    (tmp_path / "S2A.SAFE" / "GRANULE" / "L1C_T31").mkdir(parents=True)
    (tmp_path / ".hidden").write_text("x")
    out = status.list_input_products()
    assert "S3A_OL_1.SEN3" in out
    assert "scene.nc" in out
    assert "S2A.SAFE/GRANULE/L1C_T31" in out
    assert ".hidden" not in out


def test_app_version_from_file(tmp_path, monkeypatch):
    monkeypatch.setenv("POLYMER_GUI_VERSION", "dev")
    monkeypatch.setattr(status, "__file__", str(tmp_path / "setup_status.py"))
    (tmp_path / "VERSION").write_text("1.2.3\n")
    assert status.app_version() == "1.2.3"
