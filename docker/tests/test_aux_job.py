"""Lifecycle tests for the background auxiliary-data download, subprocess mocked."""
import json

import pytest

import aux_job


@pytest.fixture
def aux(tmp_path, monkeypatch):
    aux_job.configure(tmp_path)
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
