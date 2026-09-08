"""
Background download of Polymer's static auxiliary data (~1 GB).

`python -m polymer.get_auxdata` is run as a detached subprocess so the Streamlit
session is not blocked and a stalled download can be cancelled. State lives in
one file under /data/output/_run/ so it survives Streamlit reruns and tab
switches. Only one download runs at a time.

Public API:
    start()   -> bool      (False if a download is already running)
    status()  -> dict      (running / rc / elapsed_s / tail / log)
    cancel()  -> None
    clear()   -> None      (forget the last finished run)

Invoked internally as `python aux_job.py --run` to be the worker process.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

APP_DIR = Path(__file__).parent
RUN_DIR = Path("/data/output/_run")
STATE = RUN_DIR / "auxdata.json"
LOG = RUN_DIR / "auxdata.log"
RESULT = RUN_DIR / "auxdata.result.json"
AUXDATA_DIR = Path(os.environ.get("DIR_DATA", "/data")) / "auxdata"


def configure(run_dir, auxdata_dir=None) -> None:
    """Repoint all paths (used by the test suite)."""
    global RUN_DIR, STATE, LOG, RESULT, AUXDATA_DIR
    RUN_DIR = Path(run_dir)
    STATE = RUN_DIR / "auxdata.json"
    LOG = RUN_DIR / "auxdata.log"
    RESULT = RUN_DIR / "auxdata.result.json"
    if auxdata_dir is not None:
        AUXDATA_DIR = Path(auxdata_dir)


def _read_json(p: Path, default):
    try:
        return json.loads(p.read_text())
    except Exception:
        return default


def _pid_alive(pid: int) -> bool:
    try:
        os.waitpid(pid, os.WNOHANG)  # reap if it is our finished child
    except Exception:
        pass
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
        if stat.rsplit(")", 1)[1].split()[0] in ("Z", "X", "x"):  # zombie / dead
            return False
        cmd = Path(f"/proc/{pid}/cmdline").read_bytes()
        return b"aux_job" in cmd or b"get_auxdata" in cmd  # guard against PID reuse
    except Exception:
        return True


def start() -> bool:
    """Launch the download unless one is already running. Returns True if started."""
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if status()["running"]:
        return False
    RESULT.unlink(missing_ok=True)
    clear_stale_locks()  # also cleared by the worker; do it here in case it never starts
    log_fh = open(LOG, "wb")
    try:
        proc = subprocess.Popen(
            [sys.executable, str(APP_DIR / "aux_job.py"), "--run"],
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env={**os.environ},
        )
    finally:
        log_fh.close()  # the child keeps its own copy of the fd
    STATE.write_text(
        json.dumps(
            {
                "pid": proc.pid,
                "started_ts": time.time(),
                "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
        )
    )
    return True


def _tail(n: int = 400) -> str:
    try:
        return "\n".join(LOG.read_text(errors="replace").splitlines()[-n:])
    except Exception:
        return ""


def status() -> dict:
    """Snapshot for the UI. `running` is True only while the worker is alive."""
    s = _read_json(STATE, None)
    res = _read_json(RESULT, None)
    if s is None:
        return {
            "running": False,
            "rc": (res or {}).get("rc"),
            "error": (res or {}).get("error", ""),
            "started": "",
            "elapsed_s": 0,
            "tail": _tail(),
            "log": str(LOG),
        }
    alive = _pid_alive(int(s["pid"]))
    running = alive and res is None
    rc = (res or {}).get("rc")
    if not running and res is None:
        rc = 1  # process gone without writing a result (killed / container stop)
    return {
        "running": running,
        "rc": rc,
        "error": (res or {}).get("error", ""),
        "started": s.get("started", ""),
        "elapsed_s": round(time.time() - s.get("started_ts", time.time())),
        "tail": _tail(),
        "log": str(LOG),
    }


def clear() -> None:
    """Forget the last finished run so its result banner stops showing."""
    STATE.unlink(missing_ok=True)
    RESULT.unlink(missing_ok=True)


def cancel() -> None:
    s = _read_json(STATE, None)
    if s is None:
        return
    pid = int(s["pid"])
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(os.getpgid(pid), sig)
        except (OSError, ProcessLookupError):
            break
        time.sleep(0.5)
        if not _pid_alive(pid):
            break
    RESULT.write_text(json.dumps({"rc": 130, "error": "cancelled"}))


def clear_stale_locks() -> int:
    """
    Remove leftover *.lock / *.tmp files under the auxdata folder.

    core's download helper guards each file with a `<file>.lock`. If a previous
    download was killed (Cancel, container stop, Docker Desktop restart on
    Windows) the lock is orphaned and the next attempt fails with
    "Timeout on Lockfile ...". We are single-flight, so nothing legitimately
    holds these when a new download starts.
    """
    removed = 0
    for pattern in ("*.lock", "*.tmp"):
        for p in AUXDATA_DIR.rglob(pattern):
            try:
                p.unlink()
                removed += 1
                print(f"[aux_job] removed stale {p.name}", flush=True)
            except OSError:
                pass
    return removed


# The worker has no i18n; it writes a short reason code that the UI translates.
_DOWNLOAD_HOST = "download.hygeos.com"


def _dns_ok(host: str = _DOWNLOAD_HOST) -> bool:
    import socket

    try:
        socket.getaddrinfo(host, 443)
        return True
    except OSError:
        return False


def _download_once() -> int:
    try:
        return subprocess.run(
            [sys.executable, "-m", "polymer.get_auxdata"], env={**os.environ}
        ).returncode
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[aux_job] could not start the downloader: {exc}", flush=True)
        return 1


def _run() -> int:
    """Worker body: DNS check, clear stale locks, download, retry once."""
    if not _dns_ok():
        print(f"[aux_job] ERROR: cannot resolve {_DOWNLOAD_HOST} (DNS)", flush=True)
        RESULT.write_text(json.dumps({"rc": 1, "error": "dns"}))
        return 1

    clear_stale_locks()
    rc = _download_once()
    if rc != 0:
        print("[aux_job] download failed, clearing locks and retrying once", flush=True)
        clear_stale_locks()
        rc = _download_once()

    error = "" if rc == 0 else ("dns" if not _dns_ok() else "incomplete")
    RESULT.write_text(json.dumps({"rc": rc, "error": error}))
    return rc


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="run the download (worker mode)")
    if ap.parse_args().run:
        sys.exit(_run())
