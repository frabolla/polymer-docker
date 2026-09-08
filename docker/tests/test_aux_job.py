"""Lifecycle tests for the background auxiliary-data download, subprocess mocked."""
import json

import pytest

import aux_job


@pytest.fixture
def aux(tmp_path, monkeypatch):
    aux_job.configure(tmp_path, auxdata_dir=tmp_path / "auxdata")
    alive = {"v": True}
    started = []

    class FakePopen:
        def __init__(self, argv, **kw):
            self.pid = 515151
            started.append(argv)

    monkeypatch.setattr(aux_job.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(aux_job, "_pid_alive", lambda pid: alive["v"])

    aux_job._alive = alive
    aux_job._started = started
    return aux_job


def test_start_is_single_flight(aux):
    assert aux.start() is True
    assert aux.STATE.exists()
    assert aux.status()["running"] is True
    # a second start while one is running is refused
    assert aux.start() is False
    assert len(aux._started) == 1


def test_clear_stale_locks(aux, tmp_path):
    common = tmp_path / "auxdata" / "static" / "common"
    common.mkdir(parents=True)
    (common / "no2_climatology.hdf.lock").write_text("")
    (common / "LUT.hdf.tmp").write_text("partial")
    keep = common / "k_oz.csv"
    keep.write_text("real data")

    assert aux.clear_stale_locks() == 2
    assert not (common / "no2_climatology.hdf.lock").exists()
    assert not (common / "LUT.hdf.tmp").exists()
    assert keep.exists()  # real files untouched
    assert aux.clear_stale_locks() == 0  # idempotent


def test_start_clears_locks_first(aux, tmp_path):
    lock = tmp_path / "auxdata" / "static" / "common" / "x.hdf.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("")
    assert aux.start() is True
    assert not lock.exists()


def test_run_fails_fast_on_dns(aux, monkeypatch):
    monkeypatch.setattr(aux, "_dns_ok", lambda *a, **k: False)
    called = []
    monkeypatch.setattr(aux, "_download_once", lambda: called.append(1) or 0)
    rc = aux._run()
    assert rc == 1 and not called  # never attempted the download
    res = json.loads(aux.RESULT.read_text())
    assert res["rc"] == 1 and res["error"] == "dns"


def test_run_records_reason_on_incomplete(aux, monkeypatch):
    monkeypatch.setattr(aux, "_dns_ok", lambda *a, **k: True)
    monkeypatch.setattr(aux, "_download_once", lambda: 1)  # keeps failing
    monkeypatch.setattr(aux, "clear_stale_locks", lambda: 0)
    assert aux._run() == 1
    assert json.loads(aux.RESULT.read_text())["error"] == "incomplete"


def test_run_ok_clears_error(aux, monkeypatch):
    monkeypatch.setattr(aux, "_dns_ok", lambda *a, **k: True)
    monkeypatch.setattr(aux, "_download_once", lambda: 0)
    monkeypatch.setattr(aux, "clear_stale_locks", lambda: 0)
    assert aux._run() == 0
    res = json.loads(aux.RESULT.read_text())
    assert res["rc"] == 0 and res["error"] == ""


def test_status_reports_success(aux):
    aux.start()
    aux.RESULT.write_text(json.dumps({"rc": 0}))
    aux._alive["v"] = False
    st = aux.status()
    assert st["running"] is False and st["rc"] == 0


def test_status_reports_orphaned_process(aux):
    aux.start()
    aux._alive["v"] = False  # process gone, no result written
    st = aux.status()
    assert st["running"] is False and st["rc"] == 1


def test_cancel_records_result(aux):
    aux.start()
    aux.cancel()
    assert json.loads(aux.RESULT.read_text())["rc"] == 130
    aux._alive["v"] = False
    assert aux.status()["rc"] == 130


def test_clear_forgets_last_run(aux):
    aux.start()
    aux.RESULT.write_text(json.dumps({"rc": 0}))
    aux.clear()
    assert not aux.STATE.exists() and not aux.RESULT.exists()
    assert aux.status() == {
        "running": False,
        "rc": None,
        "error": "",
        "started": "",
        "elapsed_s": 0,
        "tail": "",
        "log": str(aux.LOG),
    }


def test_start_after_finish_runs_again(aux):
    aux.start()
    aux.RESULT.write_text(json.dumps({"rc": 0}))
    aux._alive["v"] = False
    # finished: a new download is allowed
    assert aux.start() is True
    assert len(aux._started) == 2
