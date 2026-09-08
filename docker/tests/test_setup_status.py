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


def _flaky_stat(monkeypatch, doomed: str):
    """Make Path.stat raise FileNotFoundError for one file name (a mid-scan race)."""
    orig = status.Path.stat

    def stat(self, *a, **k):
        if self.name == doomed:
            raise FileNotFoundError
        return orig(self, *a, **k)

    monkeypatch.setattr(status.Path, "stat", stat)


def test_auxdata_size_tolerates_vanishing_files(aux, monkeypatch):
    """A concurrent download renaming temp files must not crash the size scan."""
    _flaky_stat(monkeypatch, "no2_climatology.hdf")
    assert status.auxdata_size_mb() > 0  # counted the rest, skipped the racer


def test_verify_auxdata_tolerates_stat_errors(aux, monkeypatch):
    _flaky_stat(monkeypatch, "LUT.hdf")
    ok, problems = status.verify_auxdata()
    assert not ok and any("LUT.hdf" in p for p in problems)  # "missing", no crash


def test_list_input_products_includes_granules(tmp_path, monkeypatch):
    monkeypatch.setattr(status, "INPUT_DIR", tmp_path)
    (tmp_path / "S3A_OL_1.SEN3").mkdir()
    (tmp_path / "scene.nc").write_text("x")
    (tmp_path / "S2A.SAFE" / "GRANULE" / "L1C_T31").mkdir(parents=True)
    (tmp_path / ".hidden").write_text("x")
    (tmp_path / "PRS_L1_STD_OFFL_x.he5").write_text("x")
    (tmp_path / "PRS_L2C_STD_x.he5").write_text("x")
    out = status.list_input_products()
    assert "S3A_OL_1.SEN3" in out
    assert "scene.nc" in out
    assert "S2A.SAFE/GRANULE/L1C_T31" in out
    assert ".hidden" not in out
    assert "PRS_L1_STD_OFFL_x.he5" in out
    assert "PRS_L2C_STD_x.he5" not in out  # companion, hidden from the list


def test_app_version_from_file(tmp_path, monkeypatch):
    monkeypatch.setenv("POLYMER_GUI_VERSION", "dev")
    monkeypatch.setattr(status, "__file__", str(tmp_path / "setup_status.py"))
    (tmp_path / "VERSION").write_text("1.2.3\n")
    assert status.app_version() == "1.2.3"


def test_prisma_companion_detection(tmp_path):
    l1 = "PRS_L1_STD_OFFL_20210721102700_20210721102705_0001.he5"
    l2c = "PRS_L2C_STD_20210721102700_20210721102705_0001.he5"

    assert status.prisma_l2c_name(l1) == l2c
    assert status.prisma_l2c_name("S3A_OL_1_EFR.SEN3") is None

    (tmp_path / l1).write_bytes(b"x")
    assert status.missing_prisma_companion(tmp_path / l1) == l2c  # L2C absent

    (tmp_path / l2c).write_bytes(b"x")
    assert status.missing_prisma_companion(tmp_path / l1) is None  # both present

    (tmp_path / "scene.nc").write_bytes(b"x")
    assert status.missing_prisma_companion(tmp_path / "scene.nc") is None


def test_workdirs_default_and_override(tmp_path, monkeypatch):
    monkeypatch.setattr(status, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(status, "WORKDIRS_FILE", tmp_path / "dirs.env")
    monkeypatch.setenv("POLYMER_HOST_DIR", "/host/polymer/data")

    d = status.load_workdirs()
    assert d["input"] == "/host/polymer/data/input"
    assert d["output"] == "/host/polymer/data/output"
    assert d["custom"] is False

    status.save_workdirs("/mnt/ext/in", "  /mnt/ext/out  ")
    text = (tmp_path / "dirs.env").read_text()
    assert "POLYMER_INPUT_DIR=/mnt/ext/in" in text
    assert "POLYMER_OUTPUT_DIR=/mnt/ext/out" in text

    d = status.load_workdirs()
    assert d["input"] == "/mnt/ext/in" and d["output"] == "/mnt/ext/out"
    assert d["config"] == "/host/polymer/data/config"  # config never moves
    assert d["custom"] is True

    status.clear_workdirs()
    assert not (tmp_path / "dirs.env").exists()
    assert status.load_workdirs()["custom"] is False


def test_workdirs_no_host_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(status, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(status, "WORKDIRS_FILE", tmp_path / "dirs.env")
    monkeypatch.delenv("POLYMER_HOST_DIR", raising=False)
    d = status.load_workdirs()
    assert d["input"] == "" and d["custom"] is False
