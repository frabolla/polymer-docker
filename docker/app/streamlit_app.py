"""
Web interface for Polymer (atmospheric correction of ocean colour).

Opens in the browser at http://localhost:8501 while the container is running.
Nothing to type on a command line: every parameter is set from here.

English is the primary language; Italian can be selected in the sidebar.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

import credentials as cred
import i18n
import job_runner
import quicklook
import setup_status as status
import uploads
from params_schema import (
    ANCILLARY_SOURCES,
    COMMON_PARAMS,
    NEEDS_EXPLICIT_SENSOR,
    NORMALIZE,
    OUTPUT_FORMATS,
    SENSORS,
    WATER_MODELS,
)

APP_DIR = Path(__file__).parent
LICENCE_FILE = APP_DIR / "LICENCE.TXT"
CONFIG_DIR = Path(os.environ.get("HOME", "/data/config"))
LICENCE_FLAG = CONFIG_DIR / ".polymer_licence_accepted"
OUTPUT_DIR = Path("/data/output")
INPUT_DIR = Path("/data/input")

st.set_page_config(page_title="Polymer", page_icon="P", layout="wide")

# Hide Streamlit's own chrome (the "Deploy" button, the hamburger menu and the
# "Made with Streamlit" footer) so the page reads as a standalone tool.
st.markdown(
    """
    <style>
      [data-testid="stToolbar"] {display: none !important;}
      [data-testid="stToolbarActions"] {display: none !important;}
      [data-testid="stAppDeployButton"] {display: none !important;}
      [data-testid="stDecoration"] {display: none !important;}
      [data-testid="stStatusWidget"] {display: none !important;}
      #MainMenu {visibility: hidden !important;}
      footer {visibility: hidden !important;}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- util
def stream_command(cmd: list[str], env: dict | None = None) -> int:
    """Run `cmd`, mirror stdout/stderr into an on-screen box, return the exit code."""
    box = st.empty()
    lines: list[str] = []
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env={**os.environ, **(env or {})},
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        lines.append(line.rstrip())
        box.code("\n".join(lines[-400:]), language="text")
    proc.wait()
    return proc.returncode


# --------------------------------------------------------------------- language
def pick_language() -> None:
    """Render the language selector and apply the choice (rerun on change)."""
    saved = st.session_state.get("lang") or i18n.load_saved_lang()
    i18n.set_lang(saved)

    codes = list(i18n.LANGUAGES.keys())
    idx = codes.index(saved) if saved in codes else 0
    choice = st.sidebar.selectbox(
        i18n.t("sidebar.language"),
        codes,
        index=idx,
        format_func=lambda c: i18n.LANGUAGES[c],
        key="lang_select",
    )
    if choice != saved:
        st.session_state["lang"] = choice
        i18n.save_lang(choice)
        i18n.set_lang(choice)
        st.rerun()
    st.session_state["lang"] = choice
    i18n.set_lang(choice)


# Plain typographic status marks (no emoji).
_MARK_OK = "✓"       # check mark
_MARK_TODO = "–"     # en dash


# ------------------------------------------------------------------ licence gate
def licence_gate() -> bool:
    if LICENCE_FLAG.exists():
        return True
    st.title(i18n.t("licence.title"))
    st.caption(i18n.t("app.fork_note"))
    st.warning(i18n.t("licence.warning"))

    with st.expander(i18n.t("licence.steps_header"), expanded=True):
        st.markdown(i18n.t("licence.steps_body"))

    if LICENCE_FILE.exists():
        st.text_area("LICENCE.TXT", LICENCE_FILE.read_text(), height=320)
    agree = st.checkbox(i18n.t("licence.checkbox"))
    if st.button(i18n.t("licence.continue"), disabled=not agree, type="primary"):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        LICENCE_FLAG.write_text(datetime.now().isoformat())
        st.rerun()
    return False


# ---------------------------------------------------------------- sidebar status
def _mark(ok: bool) -> str:
    return _MARK_OK if ok else _MARK_TODO


def sidebar_status() -> None:
    st.sidebar.header(i18n.t("status.header"))

    st.sidebar.write(_mark(status.cython_modules_ok()) + " " + i18n.t("status.modules"))

    ok_aux = status.auxdata_present()
    st.sidebar.write(
        _mark(ok_aux) + " " + i18n.t("status.auxdata", size=status.auxdata_size_mb())
    )

    cs = cred.status()
    st.sidebar.write(
        _mark(cs["earthdata"])
        + " " + i18n.t("status.earthdata")
        + (f" ({cs['earthdata_login']})" if cs["earthdata"] else "")
    )
    st.sidebar.write(_mark(cs["cds"]) + " " + i18n.t("status.cds"))

    st.sidebar.divider()
    if not ok_aux:
        st.sidebar.info(i18n.t("status.need_auxdata"))
    st.sidebar.caption(i18n.t("status.folders"))
    st.sidebar.caption(i18n.t("sidebar.version", v=status.app_version()))


# --------------------------------------------------------------------- setup tab
def tab_config() -> None:
    st.subheader(i18n.t("config.aux_header"))
    st.write(i18n.t("config.aux_text"))

    ok_aux, problems = status.verify_auxdata()
    if ok_aux:
        st.success(i18n.t("config.aux_present", size=status.auxdata_size_mb()))
    elif problems and status.auxdata_size_mb() > 0:
        st.warning("\n".join("- " + p for p in problems))

    if st.button(i18n.t("config.aux_button"), type="primary"):
        rc = stream_command([sys.executable, "-m", "polymer.get_auxdata"])
        ok_after, problems_after = status.verify_auxdata()
        if rc == 0 and ok_after:
            st.success(i18n.t("config.aux_ok"))
        elif rc == 0 and not ok_after:
            st.error("\n".join([i18n.t("config.aux_fail", rc=rc)] + ["- " + p for p in problems_after]))
        else:
            st.error(i18n.t("config.aux_fail", rc=rc))

    st.divider()
    st.subheader(i18n.t("config.cred_header"))
    st.write(i18n.t("config.cred_text"))

    src = st.radio(
        i18n.t("config.cred_source"),
        options=ANCILLARY_SOURCES,
        format_func=lambda k: i18n.t(f"ancillary.{k}"),
        key="anc_source_config",
    )

    if src == "NASA":
        ed = cred.read_earthdata()
        with st.form("form_nasa"):
            login = st.text_input(i18n.t("config.nasa_user"), value=ed.get("login", ""))
            pw = st.text_input(i18n.t("config.nasa_pass"), type="password")
            c1, c2 = st.columns(2)
            save = c1.form_submit_button(i18n.t("config.nasa_save"), type="primary")
            clear = c2.form_submit_button(i18n.t("config.remove"))
        if save:
            if login and pw:
                cred.write_earthdata(login, pw)
                st.success(i18n.t("config.nasa_saved"))
                st.rerun()
            else:
                st.error(i18n.t("config.nasa_need_both"))
        if clear:
            cred.clear_earthdata()
            st.info(i18n.t("config.nasa_removed"))
            st.rerun()
        st.caption(i18n.t("config.nasa_hint"))

    elif src == "ERA5":
        cds = cred.read_cds()
        with st.form("form_cds"):
            key = st.text_input(
                i18n.t("config.cds_key"),
                value=cds.get("key", ""),
                help=i18n.t("config.cds_key_help"),
            )
            c1, c2 = st.columns(2)
            save = c1.form_submit_button(i18n.t("config.cds_save"), type="primary")
            clear = c2.form_submit_button(i18n.t("config.remove"))
        if save:
            if key.strip():
                cred.write_cds(key.strip())
                st.success(i18n.t("config.cds_saved"))
                st.rerun()
            else:
                st.error(i18n.t("config.cds_need_key"))
        if clear:
            cred.clear_cds()
            st.info(i18n.t("config.cds_removed"))
            st.rerun()
        st.caption(i18n.t("config.cds_hint"))

    else:
        st.info(i18n.t("config.cred_none"))


# -------------------------------------------------------------- job config build
def build_job_config(
    input_path: str,
    sensor: str,
    fmt: str,
    resolution: str,
    ancillary: str,
    output_name: str,
    common_vals: dict,
    advanced: dict,
) -> dict:
    # Pass the crop parameters only when the user changed them from the defaults
    # (0 / -1): some Level1 classes do not accept scol/ecol.
    _crop_defaults = {"sline": 0, "eline": -1, "scol": 0, "ecol": -1}
    l1_kwargs = {
        k: int(common_vals[k])
        for k, dflt in _crop_defaults.items()
        if k in common_vals and int(common_vals[k]) != dflt
    }
    polymer_kwargs: dict = {"multiprocessing": int(common_vals.get("multiprocessing", 0))}
    if common_vals.get("water_model"):
        polymer_kwargs["water_model"] = common_vals["water_model"]
    if common_vals.get("normalize") is not None:
        polymer_kwargs["normalize"] = int(common_vals["normalize"])
    if common_vals.get("force_initialization"):
        polymer_kwargs["force_initialization"] = True
    polymer_kwargs.update(advanced)

    return {
        "input": input_path,
        "sensor": sensor,
        "output_dir": str(OUTPUT_DIR),
        "output_name": output_name,
        "fmt": fmt,
        "resolution": resolution,
        "ancillary": ancillary,
        "l1_kwargs": l1_kwargs,
        "polymer_kwargs": polymer_kwargs,
    }


def parse_advanced(text: str) -> dict:
    """Turn 'key = value' lines into a dict (values decoded as JSON when possible)."""
    out: dict = {}
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        k, _, v = raw.partition("=")
        k, v = k.strip(), v.strip()
        try:
            out[k] = json.loads(v)
        except Exception:
            out[k] = v
    return out


# --------------------------------------------------------- running job / batch UI
def render_running(stt: dict) -> None:
    st.subheader(i18n.t("run.title"))
    if stt.get("total_in_batch", 1) > 1 or stt.get("queued"):
        st.caption(
            i18n.t(
                "run.batch_pos",
                i=stt.get("index", 1),
                n=stt.get("total_in_batch", 1),
                q=stt.get("queued", 0),
            )
        )
    st.write(i18n.t("run.processing", input=Path(stt["input"]).name))

    done, total = stt.get("blocks_done", 0), stt.get("blocks_total")
    if total:
        st.progress(min(done / total, 1.0), text=i18n.t("run.blocks", d=done, n=total))
    else:
        st.caption(i18n.t("run.blocks_nototal", d=done))
    st.caption(i18n.t("run.elapsed", s=stt.get("elapsed_s", 0)))

    st.code(job_runner.log_tail(stt["log"], 300), language="text")

    if st.button(i18n.t("run.cancel"), type="secondary"):
        job_runner.cancel()
        st.rerun()

    time.sleep(2)
    st.rerun()


def render_batch_summary() -> None:
    batch_id = st.session_state.get("last_batch")
    if not batch_id:
        return
    rows = job_runner.batch_rows(batch_id)
    if not rows:
        return
    ok = sum(1 for r in rows if r.get("result") == "ok")
    st.subheader(i18n.t("batch.title"))
    st.write(i18n.t("batch.summary", ok=ok, fail=len(rows) - ok, n=len(rows)))
    cols = ["input", "sensor", "result", "duration_s", "output"]
    disp = [
        {i18n.t(f"history.col.{c}"): (Path(str(r.get(c, ""))).name if c in ("input", "output") else r.get(c, "")) for c in cols}
        for r in rows
    ]
    st.dataframe(disp, width="stretch", hide_index=True)
    if st.button(i18n.t("batch.dismiss")):
        del st.session_state["last_batch"]
        st.rerun()
    st.divider()


def render_uploader() -> None:
    with st.expander(i18n.t("upload.header")):
        files = st.file_uploader(
            i18n.t("upload.label"),
            accept_multiple_files=True,
            type=["zip", "nc", "he5", "h5", "hdf", "n1", "l1c", "csv"],
            key="uploader",
        )
        if files and st.button(i18n.t("upload.save"), type="primary"):
            for m in uploads.save_uploads(files):
                st.write("- " + m)
            st.rerun()


# ---------------------------------------------------------------- processing tab
def tab_process() -> None:
    job_runner.poll()
    stt = job_runner.state()
    if stt.get("running"):
        render_running(stt)
        return

    render_batch_summary()

    if not status.overall_ready():
        st.warning(i18n.t("process.incomplete"))

    render_uploader()

    products = status.list_input_products()
    if not products:
        st.info(i18n.t("process.no_products"))
        return

    col_l, col_r = st.columns([2, 1])
    with col_l:
        selected = st.multiselect(
            i18n.t("process.products"),
            products,
            default=products[:1],
            help=i18n.t("process.products_help"),
        )
    with col_r:
        sensor = st.selectbox(i18n.t("process.sensor"), SENSORS, index=0)
        fmt = st.selectbox(i18n.t("process.fmt"), OUTPUT_FORMATS, index=0)

    resolution = "60"
    if sensor == "MSI":
        resolution = st.selectbox(i18n.t("process.msi_res"), ["10", "20", "60"], index=2)
    if sensor in NEEDS_EXPLICIT_SENSOR:
        st.caption(i18n.t("process.explicit_sensor", sensor=sensor))

    ancillary = st.selectbox(
        i18n.t("process.ancillary"),
        ANCILLARY_SOURCES,
        format_func=lambda k: i18n.t(f"ancillary.{k}"),
        index=0,
    )

    st.markdown(i18n.t("process.common_params"))
    common_vals: dict = {}
    cols = st.columns(3)
    for i, p in enumerate(COMMON_PARAMS):
        with cols[i % 3]:
            common_vals[p["name"]] = st.number_input(
                i18n.t(f"param.{p['name']}.label"),
                value=int(p["default"]),
                step=1,
                help=i18n.t(f"param.{p['name']}.help"),
                key=f"cp_{p['name']}",
            )
    c1, c2, c3 = st.columns(3)
    common_vals["water_model"] = c1.selectbox(
        i18n.t("process.water_model"),
        WATER_MODELS,
        format_func=lambda k: i18n.t(f"watermodel.{k}"),
        index=0,
    )
    common_vals["normalize"] = c2.selectbox(
        i18n.t("process.normalize"),
        NORMALIZE,
        format_func=lambda k: i18n.t(f"normalize.{k}"),
        index=0,
    )
    common_vals["force_initialization"] = c3.checkbox(i18n.t("process.force_init"), value=False)

    with st.expander(i18n.t("process.advanced")):
        st.caption(i18n.t("process.advanced_help"))
        advanced_text = st.text_area("advanced", value="", height=140, label_visibility="collapsed")

    output_name = ""
    if len(selected) == 1:
        output_name = st.text_input(
            i18n.t("process.output_name"),
            value="",
            help=i18n.t("process.output_name_help"),
        )

    if st.button(i18n.t("process.run"), type="primary", disabled=not selected):
        advanced = parse_advanced(advanced_text)
        cfgs = [
            build_job_config(
                input_path=str(INPUT_DIR / name),
                sensor=sensor,
                fmt=fmt,
                resolution=resolution,
                ancillary=ancillary,
                output_name=output_name if len(selected) == 1 else "",
                common_vals=common_vals,
                advanced=advanced,
            )
            for name in selected
        ]
        st.session_state["last_batch"] = job_runner.enqueue(cfgs, version=status.app_version())
        st.rerun()


# ------------------------------------------------------------------- guide tab
def tab_guide() -> None:
    st.write(i18n.t("guide.intro"))

    st.subheader(i18n.t("guide.first_header"))
    st.markdown(i18n.t("guide.first_body"))

    st.divider()
    st.subheader(i18n.t("guide.update_header"))
    st.markdown(i18n.t("guide.update_body"))

    st.divider()
    st.subheader(i18n.t("guide.about_header"))
    st.markdown(i18n.t("guide.about_body"))


# ------------------------------------------------------------------- results tab
def _output_files() -> list[Path]:
    if not OUTPUT_DIR.exists():
        return []
    files = [
        p for p in OUTPUT_DIR.iterdir()
        if p.is_file() and p.suffix in (".nc", ".hdf") and not p.name.startswith("_")
    ]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def tab_results() -> None:
    files = _output_files()
    if not files:
        st.info(i18n.t("results.none"))
        return

    pick = st.selectbox(
        i18n.t("results.pick"),
        files,
        format_func=lambda p: p.name,
    )
    when = datetime.fromtimestamp(pick.stat().st_mtime).isoformat(timespec="seconds")
    st.caption(i18n.t("results.info", name=pick.name, size=pick.stat().st_size / 1e6, when=when))

    try:
        vars_ = quicklook.list_2d_vars(str(pick))
    except Exception as exc:
        st.caption(i18n.t("process.preview_unavailable", exc=exc))
        return

    choice = st.selectbox(
        i18n.t("results.variable"),
        ["__auto__"] + vars_,
        format_func=lambda v: i18n.t("results.auto") if v == "__auto__" else v,
    )
    try:
        png = CONFIG_DIR / "_preview.png"
        desc = quicklook.make_png(
            str(pick), str(png), var=None if choice == "__auto__" else choice
        )
        st.image(str(png), caption=desc, width="stretch")
    except Exception as exc:
        st.caption(i18n.t("process.preview_unavailable", exc=exc))


# ------------------------------------------------------------------ history tab
def tab_history() -> None:
    rows = job_runner.read_history()
    if not rows:
        st.info(i18n.t("history.empty"))
        return
    cols = ["when", "input", "sensor", "format", "duration_s", "result", "version"]
    display = [
        {
            i18n.t(f"history.col.{c}"): (
                Path(str(r.get(c, ""))).name if c == "input" else r.get(c, "")
            )
            for c in cols
        }
        for r in rows
    ]
    st.dataframe(display, width="stretch", hide_index=True)


# ----------------------------------------------------------------------------- main
def main() -> None:
    pick_language()
    if not licence_gate():
        return
    job_runner.poll()  # keep job state fresh regardless of the active tab
    sidebar_status()
    st.title("Polymer")
    st.caption(i18n.t("app.caption"))
    st.caption(i18n.t("app.fork_note"))

    t_proc, t_conf, t_guide, t_results, t_hist = st.tabs(
        [
            i18n.t("tab.process"),
            i18n.t("tab.config"),
            i18n.t("tab.guide"),
            i18n.t("tab.results"),
            i18n.t("tab.history"),
        ]
    )
    with t_proc:
        tab_process()
    with t_conf:
        tab_config()
    with t_guide:
        tab_guide()
    with t_results:
        tab_results()
    with t_hist:
        tab_history()


if __name__ == "__main__":
    main()
