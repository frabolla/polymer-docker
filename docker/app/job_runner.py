"""
Background job runner for Polymer processing.

A job is a subprocess (`polymer_job.py`) started detached, with its output going
to a log file. State lives in files under /data/output/_run/ so a job survives
Streamlit reruns, tab switches and language changes. One job runs at a time;
extra jobs wait in a queue (used for batch processing).

Public API:
    enqueue(cfgs, version="")  -> batch_id
    poll()                     -> None      (heartbeat: finalize done jobs, start next)
    state()                    -> dict      (what to show in the UI)
    cancel()                   -> None      (kill current job, clear the queue)
    batch_rows(batch_id)       -> list[dict]
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).parent
OUTPUT_DIR = Path("/data/output")
RUN_DIR = OUTPUT_DIR / "_run"
CURRENT = RUN_DIR / "current.json"
QUEUE = RUN_DIR / "queue.json"
LOCK = RUN_DIR / ".lock"
JOBS_LOG = OUTPUT_DIR / "_jobs.log"

# Housekeeping limits.
KEEP_RUNS = 25          # per-run file sets kept under _run/
JOBS_LOG_MAX_LINES = 500

_PROC_RE = re.compile(r"Processing block:")
_TOTAL_RE = re.compile(r"BLOCKS_TOTAL (\d+)")


def configure(output_dir) -> None:
    """Repoint all paths at `output_dir` (used by the test suite)."""
    global OUTPUT_DIR, RUN_DIR, CURRENT, QUEUE, LOCK, JOBS_LOG
    OUTPUT_DIR = Path(output_dir)
    RUN_DIR = OUTPUT_DIR / "_run"
    CURRENT = RUN_DIR / "current.json"
    QUEUE = RUN_DIR / "queue.json"
    LOCK = RUN_DIR / ".lock"
    JOBS_LOG = OUTPUT_DIR / "_jobs.log"


# ------------------------------------------------------------------ small helpers
def _read_json(p: Path, default):
    try:
        return json.loads(p.read_text())
    except Exception:
        return default


def _write_json(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp.replace(p)


def _pid_alive(pid: int) -> bool:
    # Reap it if it is our (finished) child, so it does not linger as a zombie.
    try:
        os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        pass
    except Exception:
        pass
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
        state = stat.rsplit(")", 1)[1].split()[0]
        if state in ("Z", "X", "x"):  # zombie / dead
            return False
        cmd = Path(f"/proc/{pid}/cmdline").read_bytes()
        return b"polymer_job" in cmd  # guard against PID reuse
    except Exception:
        return True


class _Lock:
    """Best-effort exclusive lock; steals a lock older than 30 s."""

    def __enter__(self):
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        for _ in range(50):
            try:
                fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(time.time()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - float(LOCK.read_text() or 0) > 30:
                        LOCK.unlink(missing_ok=True)
                        continue
                except Exception:
                    LOCK.unlink(missing_ok=True)
                    continue
                time.sleep(0.1)
        return self

    def __exit__(self, *exc):
        LOCK.unlink(missing_ok=True)


# ------------------------------------------------------------------- job history
def _append_history(row: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with JOBS_LOG.open("a") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_history() -> list[dict]:
    if not JOBS_LOG.exists():
        return []
    rows = []
    for ln in JOBS_LOG.read_text().splitlines():
        try:
            rows.append(json.loads(ln))
        except Exception:
            pass
    return rows[::-1]


def batch_rows(batch_id: str) -> list[dict]:
    return [r for r in read_history() if r.get("batch_id") == batch_id][::-1]


# --------------------------------------------------------------------- lifecycle
def enqueue(cfgs: list[dict], version: str = "") -> str:
    batch_id = uuid.uuid4().hex[:8]
    total = len(cfgs)
    items = []
    for i, cfg in enumerate(cfgs, 1):
        items.append(
            {
                "run_id": uuid.uuid4().hex[:12],
                "cfg": cfg,
                "batch_id": batch_id,
                "index": i,
                "total": total,
                "version": version,
            }
        )
    with _Lock():
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        _write_json(RUN_DIR / f"batch_{batch_id}.json", items)  # for "re-run failed"
        q = _read_json(QUEUE, [])
        q.extend(items)
        _write_json(QUEUE, q)
    poll()
    return batch_id


def failed_cfgs(batch_id: str) -> list[dict]:
    """The job configs of the failed runs in `batch_id` (for a re-run)."""
    items = _read_json(RUN_DIR / f"batch_{batch_id}.json", [])
    if not items:
        return []
    bad = {r["run_id"] for r in batch_rows(batch_id) if r.get("result") != "ok"}
    return [it["cfg"] for it in items if it["run_id"] in bad]


def _start(item: dict) -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rid = item["run_id"]
    cfg_path = RUN_DIR / f"{rid}.cfg.json"
    log_path = RUN_DIR / f"{rid}.log"
    res_path = RUN_DIR / f"{rid}.result.json"
    _write_json(cfg_path, item["cfg"])

    res_path.unlink(missing_ok=True)  # clear any result from a previous run_id collision
    log_fh = open(log_path, "wb")
    try:
        proc = subprocess.Popen(
            [
                sys.executable,
                str(APP_DIR / "polymer_job.py"),
                "--config", str(cfg_path),
                "--run-id", rid,
                "--result", str(res_path),
            ],
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env={**os.environ},
        )
    finally:
        log_fh.close()  # the child holds its own copy of the fd
    _write_json(
        CURRENT,
        {
            **item,
            "pid": proc.pid,
            "log": str(log_path),
            "result": str(res_path),
            "started": datetime.now().isoformat(timespec="seconds"),
            "started_ts": time.time(),
        },
    )


def _finalize(cur: dict) -> None:
    res = _read_json(Path(cur["result"]), {})
    rc = res.get("rc")
    err = res.get("error") or ""
    if rc is None:
        # the process ended without writing a result (container stopped, OOM kill…)
        rc = 1
        err = err or (
            "The job did not finish — the container was stopped, or it was killed "
            "(often out of memory: raise the memory limit in Docker Desktop → "
            "Settings → Resources)."
        )
    row = {
        "when": cur.get("started", datetime.now().isoformat(timespec="seconds")),
        "input": cur["cfg"].get("input", ""),
        "sensor": cur["cfg"].get("sensor", "auto"),
        "format": cur["cfg"].get("fmt", ""),
        "duration_s": round(time.time() - cur.get("started_ts", time.time()), 1),
        "result": "ok" if rc == 0 else f"error ({rc})",
        "output": res.get("output") or "",
        "error": err,
        "run_id": cur["run_id"],
        "batch_id": cur.get("batch_id", ""),
        "version": cur.get("version", ""),
    }
    _append_history(row)
    CURRENT.unlink(missing_ok=True)
    _prune()


def _prune() -> None:
    """Cap the size of _run/ and _jobs.log so they do not grow forever."""
    try:
        cfgs = sorted(RUN_DIR.glob("*.cfg.json"), key=lambda p: p.stat().st_mtime)
        for old in cfgs[:-KEEP_RUNS]:
            rid = old.name[: -len(".cfg.json")]
            for suffix in (".cfg.json", ".log", ".result.json", ".result.json.tmp"):
                (RUN_DIR / f"{rid}{suffix}").unlink(missing_ok=True)
        batches = sorted(RUN_DIR.glob("batch_*.json"), key=lambda p: p.stat().st_mtime)
        for old in batches[:-KEEP_RUNS]:
            old.unlink(missing_ok=True)
    except Exception:
        pass
    try:
        if JOBS_LOG.exists():
            lines = JOBS_LOG.read_text().splitlines()
            if len(lines) > JOBS_LOG_MAX_LINES:
                JOBS_LOG.write_text("\n".join(lines[-JOBS_LOG_MAX_LINES:]) + "\n")
    except Exception:
        pass


def poll() -> None:
    """Heartbeat: finalize a finished job and start the next queued one."""
    with _Lock():
        cur = _read_json(CURRENT, None)
        if cur is not None:
            done = Path(cur["result"]).exists() or not _pid_alive(int(cur["pid"]))
            if not done:
                return  # still running
            _finalize(cur)

        q = _read_json(QUEUE, [])
        if q:
            nxt = q.pop(0)
            _write_json(QUEUE, q)
            _start(nxt)


def cancel() -> None:
    with _Lock():
        cur = _read_json(CURRENT, None)
        _write_json(QUEUE, [])
        if cur is None:
            return
        pid = int(cur["pid"])
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(os.getpgid(pid), sig)
            except (OSError, ProcessLookupError):
                break
            time.sleep(0.5)
            if not _pid_alive(pid):
                break
        # Record the cancellation.
        Path(cur["result"]).write_text(
            json.dumps({"run_id": cur["run_id"], "rc": 130, "output": None, "error": "cancelled"})
        )
        _finalize(cur)


def _progress(log_path: str) -> tuple[int, int | None]:
    try:
        text = Path(log_path).read_text(errors="replace")
    except Exception:
        return 0, None
    done = len(_PROC_RE.findall(text))
    m = _TOTAL_RE.search(text)
    total = int(m.group(1)) if m else None
    return done, total


def log_tail(log_path: str, n: int = 400) -> str:
    try:
        lines = Path(log_path).read_text(errors="replace").splitlines()
        return "\n".join(lines[-n:])
    except Exception:
        return ""


def state() -> dict:
    """Snapshot for the UI. Call poll() first."""
    cur = _read_json(CURRENT, None)
    q = _read_json(QUEUE, [])
    if cur is None:
        return {"running": False, "queued": len(q)}
    done, total = _progress(cur["log"])
    return {
        "running": True,
        "run_id": cur["run_id"],
        "input": cur["cfg"].get("input", ""),
        "sensor": cur["cfg"].get("sensor", "auto"),
        "batch_id": cur.get("batch_id", ""),
        "index": cur.get("index", 1),
        "total_in_batch": cur.get("total", 1),
        "queued": len(q),
        "started": cur.get("started", ""),
        "elapsed_s": round(time.time() - cur.get("started_ts", time.time())),
        "blocks_done": done,
        "blocks_total": total,
        "log": cur["log"],
    }
