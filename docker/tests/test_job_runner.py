"""State-machine tests for job_runner, with the subprocess mocked out."""
import json

import pytest

import job_runner


@pytest.fixture
def runner(tmp_path, monkeypatch):
    job_runner.configure(tmp_path)
    alive = {"v": True}
    started = []

    class FakePopen:
        def __init__(self, argv, **kw):
            self.pid = 424242
            self.argv = argv
            started.append(argv)

    monkeypatch.setattr(job_runner.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(job_runner, "_pid_alive", lambda pid: alive["v"])

    def finish(run_id, rc, output=""):
        (job_runner.RUN_DIR / f"{run_id}.result.json").write_text(
            json.dumps({"run_id": run_id, "rc": rc, "output": output, "error": "" if rc == 0 else "boom"})
        )
        alive["v"] = False
        job_runner.poll()
        alive["v"] = True

    job_runner._runner_started = started
    job_runner._runner_finish = finish
    return job_runner


def _cfg(name):
    return {"input": f"/data/input/{name}", "sensor": "auto", "fmt": "netcdf4"}


def test_queue_runs_sequentially(runner):
    bid = runner.enqueue([_cfg("A"), _cfg("B")], version="1.0")
    st = runner.state()
    assert st["running"] and st["total_in_batch"] == 2 and st["queued"] == 1

    first = runner.state()["run_id"]
    runner._runner_finish(first, 0)

    st = runner.state()
    assert st["running"] and st["queued"] == 0  # second job started
    runner._runner_finish(st["run_id"], 1)

    assert not runner.state()["running"]
    hist = runner.read_history()
    assert len(hist) == 2
    assert {h["result"] for h in hist} == {"ok", "error (1)"}
    assert all(h["version"] == "1.0" and h["batch_id"] == bid for h in hist)


def test_cancel_clears_queue_and_records(runner):
    runner.enqueue([_cfg("A"), _cfg("B"), _cfg("C")])
    runner.cancel()
    assert not runner.state()["running"]
    assert runner.state()["queued"] == 0
    hist = runner.read_history()
    assert hist and hist[0]["result"].startswith("error")


def test_failed_cfgs_for_rerun(runner):
    bid = runner.enqueue([_cfg("A"), _cfg("B")])
    runner._runner_finish(runner.state()["run_id"], 1)   # A fails
    runner._runner_finish(runner.state()["run_id"], 0)   # B ok
    failed = runner.failed_cfgs(bid)
    assert [c["input"] for c in failed] == ["/data/input/A"]


def test_prune_keeps_recent(runner, monkeypatch):
    monkeypatch.setattr(job_runner, "KEEP_RUNS", 3)
    for i in range(8):
        (job_runner.RUN_DIR / f"r{i}.cfg.json").parent.mkdir(parents=True, exist_ok=True)
        (job_runner.RUN_DIR / f"r{i}.cfg.json").write_text("{}")
        (job_runner.RUN_DIR / f"r{i}.log").write_text("x")
    job_runner._prune()
    left = sorted(job_runner.RUN_DIR.glob("*.cfg.json"))
    assert len(left) == 3


def test_jobs_log_is_capped(runner, monkeypatch):
    monkeypatch.setattr(job_runner, "JOBS_LOG_MAX_LINES", 5)
    job_runner.JOBS_LOG.write_text("\n".join(f'{{"n":{i}}}' for i in range(50)) + "\n")
    job_runner._prune()
    assert len(job_runner.JOBS_LOG.read_text().splitlines()) == 5
