"""
Web interface for Polymer (atmospheric correction of ocean colour).

Opens in the browser at http://localhost:8501 while the container is running.
Nothing to type on a command line: every parameter is set from here.

Polymer's job is atmospheric correction only. The deliverable is the corrected
Level-2 image file (HDF by default); the small preview is just a visual check.

English is the primary language; Italian can be selected in the sidebar.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

import aux_job
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
from sound import chime_wav_bytes

APP_DIR = Path(__file__).parent
LICENCE_FILE = APP_DIR / "LICENCE.TXT"
CONFIG_DIR = Path(os.environ.get("HOME", "/data/config"))
LICENCE_FLAG = CONFIG_DIR / ".polymer_licence_accepted"
OUTPUT_DIR = Path("/data/output")
INPUT_DIR = Path("/data/input")

# Host-side path of the folder that holds input/ output/ config/ (set by the
# launcher via docker-compose). Empty when the container was started by hand.
HOST_DIR = os.environ.get("POLYMER_HOST_DIR", "").strip()

st.set_page_config(
    page_title="Polymer", page_icon=":material/water_drop:", layout="wide"
)

# A plain water-drop mark (no official Polymer logo ships with the source).
_LOGO_SVG = (
    "<svg width='34' height='34' viewBox='0 0 24 24' fill='none' "
    "xmlns='http://www.w3.org/2000/svg'><path d='M12 2.5c4 5 6.5 8.2 6.5 11.4A6.5 "
    "6.5 0 0 1 5.5 13.9C5.5 10.7 8 7.5 12 2.5Z' fill='#2E7D9A'/>"
    "<path d='M9.2 12.4c0 2 1.5 3.4 3.3 3.6' stroke='#fff' stroke-width='1.4' "
    "stroke-linecap='round'/></svg>"
)

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
      .polymer-head {display:flex; align-items:center; gap:.6rem; margin-bottom:.1rem;}
      .polymer-head h1 {margin:0; font-size:2.1rem;}
      .polymer-foot {margin-top:2.5rem; padding-top:.6rem; border-top:1px solid #e6e6e6;
                     color:#8a8a8a; font-size:.78rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


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


def _config_steps() -> list[tuple[bool, str]]:
    """(done, label) for each thing the user must set up before a run."""
    cs = cred.status()
    return [
        (status.cython_modules_ok(), i18n.t("status.modules")),
        (status.auxdata_present(), i18n.t("check.auxdata")),
        (cs["earthdata"] or cs["cds"], i18n.t("check.creds")),
    ]


def sidebar_status() -> None:
    st.sidebar.header(i18n.t("status.header"))
    for done, label in _config_steps():
        st.sidebar.write(_mark(done) + " " + label)

    cs = cred.status()
    if cs["earthdata"]:
        st.sidebar.caption(i18n.t("status.earthdata") + f": {cs['earthdata_login']}")
    if cs["cds"]:
        st.sidebar.caption(i18n.t("status.cds") + ": " + i18n.t("check.saved_short"))

    st.sidebar.divider()
    if not status.auxdata_present():
        st.sidebar.info(i18n.t("status.need_auxdata"))
    st.sidebar.caption(i18n.t("sidebar.freespace", mb=status.free_space_mb()))
    st.sidebar.caption(i18n.t("sidebar.version", v=status.app_version()))


# --------------------------------------------------------------- working folders
def _host_path(sub: str) -> str:
    if HOST_DIR:
        return str(Path(HOST_DIR) / sub)
    return f"/data/{sub}   ({i18n.t('folders.in_container')})"


def render_folders(context: str) -> None:
    """Show the on-disk locations of the work folders, with copy buttons."""
    with st.expander(i18n.t("folders.header"), expanded=False):
        st.caption(i18n.t("folders.open_hint"))
        st.write("**" + i18n.t("folders.input") + "**")
        st.code(_host_path("input"), language="text")
        if context != "input_only":
            st.write("**" + i18n.t("folders.output") + "**")
            st.code(_host_path("output"), language="text")
        st.write("**" + i18n.t("folders.config") + "**")
        st.code(_host_path("config"), language="text")
        if not HOST_DIR:
            st.caption(i18n.t("folders.container_note"))


# --------------------------------------------------------------------- setup tab
def _cred_box(kind: str) -> None:
    """One bordered credential panel: current state + Save / Verify / Remove."""
    with st.container(border=True):
        if kind == "NASA":
            st.markdown("**" + i18n.t("status.earthdata") + "**")
            ed = cred.read_earthdata()
            saved = bool(ed.get("login"))
            if saved:
                st.success(i18n.t("config.saved_as", who=ed.get("login", "")))
            else:
                st.caption(i18n.t("config.not_saved"))
            with st.form("form_nasa"):
                login = st.text_input(i18n.t("config.nasa_user"), value=ed.get("login", ""))
                pw = st.text_input(i18n.t("config.nasa_pass"), type="password")
                b1, b2 = st.columns(2)
                save = b1.form_submit_button(i18n.t("config.nasa_save"), type="primary")
                verify = b2.form_submit_button(i18n.t("config.cred_test"))
            if verify:
                _show_cred_test(cred.test_earthdata(login, pw))
            if save:
                if login and pw:
                    cred.write_earthdata(login, pw)
                    st.success(i18n.t("config.nasa_saved"))
                    st.rerun()
                else:
                    st.error(i18n.t("config.nasa_need_both"))
            if saved and st.button(i18n.t("config.remove"), key="rm_nasa"):
                cred.clear_earthdata()
                st.info(i18n.t("config.nasa_removed"))
                st.rerun()
            st.caption(i18n.t("config.nasa_hint"))

        elif kind == "ERA5":
            st.markdown("**" + i18n.t("status.cds") + "**")
            cds = cred.read_cds()
            saved = bool(cds.get("key"))
            if saved:
                st.success(i18n.t("config.saved_as", who=i18n.t("check.saved_short")))
            else:
                st.caption(i18n.t("config.not_saved"))
            with st.form("form_cds"):
                key = st.text_input(
                    i18n.t("config.cds_key"),
                    value=cds.get("key", ""),
                    help=i18n.t("config.cds_key_help"),
                )
                b1, b2 = st.columns(2)
                save = b1.form_submit_button(i18n.t("config.cds_save"), type="primary")
                verify = b2.form_submit_button(i18n.t("config.cred_test"))
            if verify:
                _show_cred_test(cred.test_cds(key.strip()))
            if save:
                if key.strip():
                    cred.write_cds(key.strip())
                    st.success(i18n.t("config.cds_saved"))
                    st.rerun()
                else:
                    st.error(i18n.t("config.cds_need_key"))
            if saved and st.button(i18n.t("config.remove"), key="rm_cds"):
                cred.clear_cds()
                st.info(i18n.t("config.cds_removed"))
                st.rerun()
            st.caption(i18n.t("config.cds_hint"))


def tab_config() -> None:
    # 1. what this tab is for
    st.info(i18n.t("config.intro"))

    # 2. static auxiliary data (downloaded once, by the user)
    st.subheader(i18n.t("config.aux_header"))
    st.write(i18n.t("config.aux_text"))

    ok_aux, problems = status.verify_auxdata()
    if ok_aux:
        st.success(i18n.t("config.aux_present", size=status.auxdata_size_mb()))
    elif problems and status.auxdata_size_mb() > 0:
        st.warning("\n".join("- " + p for p in problems))

    free = status.free_space_mb()
    if free < 2000:
        st.warning(i18n.t("config.low_disk", mb=free))

    aux = aux_job.status()
    if aux["running"]:
        st.info(i18n.t("config.aux_running", s=aux["elapsed_s"]))
        st.progress(0.0, text=i18n.t("run.phase_download"))
        if aux["tail"]:
            with st.expander(i18n.t("config.aux_log"), expanded=False):
                st.code(aux["tail"], language="text")
        if st.button(i18n.t("config.aux_cancel")):
            aux_job.cancel()
            st.rerun()
        time.sleep(2)
        st.rerun()
    else:
        if aux["rc"] is not None:
            if aux["rc"] == 0 and ok_aux:
                st.success(i18n.t("config.aux_ok"))
            elif aux["rc"] == 130:
                st.warning(i18n.t("config.aux_cancelled"))
            else:
                st.error(
                    "\n".join(
                        [i18n.t("config.aux_fail", rc=aux["rc"])]
                        + ["- " + p for p in problems]
                    )
                )
            if aux["tail"]:
                with st.expander(i18n.t("config.aux_log")):
                    st.code(aux["tail"], language="text")
            if st.button(i18n.t("config.aux_dismiss")):
                aux_job.clear()
                st.rerun()
        if st.button(
            i18n.t("config.aux_button"), type="primary", disabled=free < 500
        ):
            if aux_job.start():
                st.rerun()

    st.divider()

    # 3. meteorological-data credentials (saved and reused)
    st.subheader(i18n.t("config.cred_header"))
    st.write(i18n.t("config.cred_text"))
    st.caption(i18n.t("config.cred_persist"))

    src = st.radio(
        i18n.t("config.cred_source"),
        options=["NASA", "ERA5"],
        format_func=lambda k: i18n.t(f"ancillary.{k}"),
        horizontal=True,
        key="anc_source_config",
    )
    _cred_box(src)

    st.divider()
    render_folders("all")


def _show_cred_test(result: tuple[str, str]) -> None:
    verdict, msg = result
    if verdict == "ok":
        st.success(i18n.t("config.cred_test_ok"))
    elif verdict == "bad":
        st.error(i18n.t("config.cred_test_bad", msg=msg))
    else:
        st.info(i18n.t("config.cred_test_skip", msg=msg))


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
def _phase(log_text: str, blocks_done: int) -> str:
    """A one-line human description of what the job is doing right now."""
    if blocks_done > 0:
        return i18n.t("run.phase_processing")
    low = log_text.lower()
    if "download" in low and ("era5" in low or "meteo" in low or "ancillary" in low):
        return i18n.t("run.phase_meteo")
    if "initializing output" in low or "starting processing" in low:
        return i18n.t("run.phase_starting")
    return i18n.t("run.phase_reading")


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

    log_text = job_runner.log_tail(stt["log"], 400)
    done, total = stt.get("blocks_done", 0), stt.get("blocks_total")
    elapsed = stt.get("elapsed_s", 0)

    st.markdown("**" + _phase(log_text, done) + "**")
    if total:
        frac = min(done / total, 1.0)
        eta = ""
        if done:
            eta = "  ·  " + i18n.t("run.eta", s=int(elapsed / done * (total - done)))
        st.progress(frac, text=i18n.t("run.blocks", d=done, n=total) + eta)
    else:
        st.progress(
            min(0.05 + 0.03 * done, 0.9),
            text=(
                i18n.t("run.blocks_nototal", d=done)
                if done
                else i18n.t("run.phase_meteo")
            ),
        )
    st.caption(i18n.t("run.elapsed", s=elapsed))

    with st.expander(i18n.t("run.log"), expanded=False):
        st.code(log_text, language="text")

    if st.button(i18n.t("run.cancel"), type="secondary"):
        job_runner.cancel()
        st.rerun()

    time.sleep(2)
    st.rerun()


def render_last_result() -> None:
    """Big success / failure panel for the most recent batch, with a chime."""
    batch_id = st.session_state.get("last_batch")
    if not batch_id:
        return
    rows = job_runner.batch_rows(batch_id)
    if not rows:
        return
    ok_rows = [r for r in rows if r.get("result") == "ok"]
    fail_rows = [r for r in rows if r.get("result") != "ok"]

    if ok_rows and not fail_rows:
        st.success(i18n.t("done.title", n=len(ok_rows)))
    elif ok_rows:
        st.warning(i18n.t("done.partial", ok=len(ok_rows), fail=len(fail_rows)))
    else:
        st.error(i18n.t("done.failed", n=len(fail_rows)))

    # Play the chime once, on the first render after the batch finishes.
    played_key = f"chime_{batch_id}"
    if ok_rows and not st.session_state.get(played_key):
        st.session_state[played_key] = True
        st.audio(chime_wav_bytes(), format="audio/wav", autoplay=True)

    for r in ok_rows:
        out = Path(str(r.get("output", "")))
        st.markdown("**" + i18n.t("done.file", name=out.name) + "**")
        data_path = OUTPUT_DIR / out.name
        if data_path.exists() and data_path.stat().st_size <= 400 * 1e6:
            st.download_button(
                i18n.t("done.download"),
                data=data_path.read_bytes(),
                file_name=out.name,
                mime="application/octet-stream",
                key=f"dl_{r['run_id']}",
            )
        st.caption(i18n.t("done.results_tab"))

    for r in fail_rows:
        if r.get("error"):
            st.error(f"**{Path(str(r.get('input', ''))).name}** — {r['error']}")

    render_folders("output_only")

    failed = job_runner.failed_cfgs(batch_id)
    c1, c2 = st.columns(2)
    if failed and c1.button(i18n.t("batch.rerun_failed", n=len(failed)), type="primary"):
        st.session_state["last_batch"] = job_runner.enqueue(
            failed, version=status.app_version()
        )
        st.rerun()
    if c2.button(i18n.t("batch.dismiss")):
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


def _autodetect_sensor(name: str) -> str | None:
    """Polymer's file-name-based sensor detection (no file is opened)."""
    try:
        from polymer.level1 import Level1

        return Level1(str(INPUT_DIR / name)).sensor
    except Exception:
        return None


def render_getting_started() -> None:
    """Numbered checklist shown until the setup is complete."""
    with st.container(border=True):
        st.markdown("### " + i18n.t("process.checklist_header"))
        st.caption(i18n.t("process.checklist_intro"))
        steps = _config_steps()
        for n, (done, label) in enumerate(steps, 1):
            st.markdown(f"{_mark(done)} **{n}.** {label}")
        if not all(d for d, _ in steps):
            st.info(i18n.t("process.go_setup"))


# ---------------------------------------------------------------- processing tab
def tab_process() -> None:
    job_runner.poll()
    stt = job_runner.state()
    if stt.get("running"):
        render_running(stt)
        return

    render_last_result()

    if not status.overall_ready() or not (
        cred.status()["earthdata"] or cred.status()["cds"]
    ):
        render_getting_started()

    render_uploader()

    products = status.list_input_products()
    if not products:
        st.info(i18n.t("process.no_products"))
        render_folders("input_only")
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
        fmt = st.selectbox(
            i18n.t("process.fmt"),
            OUTPUT_FORMATS,
            index=0,
            format_func=lambda f: i18n.t(f"fmt.{f}"),
            help=i18n.t("process.fmt_help"),
        )

    resolution = "60"
    if sensor == "MSI":
        resolution = st.selectbox(i18n.t("process.msi_res"), ["10", "20", "60"], index=2)
    if sensor in NEEDS_EXPLICIT_SENSOR:
        st.caption(i18n.t("process.explicit_sensor", sensor=sensor))
    if sensor == "auto" and len(selected) == 1:
        detected = _autodetect_sensor(selected[0])
        if detected:
            st.caption(i18n.t("process.detected", sensor=detected))
        else:
            st.caption(i18n.t("process.detect_fail"))

    ancillary = st.selectbox(
        i18n.t("process.ancillary"),
        ANCILLARY_SOURCES,
        format_func=lambda k: i18n.t(f"ancillary.{k}"),
        index=0,
        help=i18n.t("process.ancillary_help"),
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

    # PRISMA needs the L1 *and* its L2C companion, plus meteo credentials.
    prisma_block = False
    prisma_selected = any(
        sensor == "PRISMA" or Path(n).name.startswith("PRS_L1_STD_OFFL_")
        for n in selected
    )
    for name in selected:
        if sensor == "PRISMA" or Path(name).name.startswith("PRS_L1_STD_OFFL_"):
            companion = status.missing_prisma_companion(INPUT_DIR / name)
            if companion:
                st.error(
                    i18n.t(
                        "process.prisma_needs_pair",
                        product=Path(name).name,
                        companion=companion,
                    )
                )
                prisma_block = True
    if prisma_selected and not cred.status()["earthdata"] and not cred.status()["cds"]:
        st.error(i18n.t("process.prisma_needs_creds"))
        prisma_block = True

    free = status.free_space_mb()
    if free < 2000:
        st.warning(i18n.t("process.low_disk", mb=free))

    if st.button(
        i18n.t("process.run"),
        type="primary",
        disabled=not selected or free < 500 or prisma_block,
    ):
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
        for k in list(st.session_state):
            if k.startswith("chime_"):
                del st.session_state[k]
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


@st.cache_data(show_spinner=False, max_entries=2)
def _file_bytes(path: str, mtime: float, size: int) -> bytes:
    return Path(path).read_bytes()


def tab_results() -> None:
    files = _output_files()
    if not files:
        st.info(i18n.t("results.none"))
        render_folders("output_only")
        return

    pick = st.selectbox(
        i18n.t("results.pick"),
        files,
        format_func=lambda p: p.name,
    )
    stat = pick.stat()
    size_mb = stat.st_size / 1e6
    when = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    st.caption(i18n.t("results.info", name=pick.name, size=size_mb, when=when))

    running = job_runner.state().get("running")
    if size_mb <= 400 and not running:
        st.download_button(
            i18n.t("results.download"),
            data=_file_bytes(str(pick), stat.st_mtime, stat.st_size),
            file_name=pick.name,
            mime="application/x-netcdf" if pick.suffix == ".nc" else "application/octet-stream",
        )
    elif size_mb > 400:
        st.caption(i18n.t("results.too_big", size=size_mb))

    render_folders("output_only")

    # Optional visual check that the correction ran — not a mapping tool.
    with st.expander(i18n.t("results.preview_header"), expanded=False):
        st.caption(i18n.t("results.preview_hint"))
        if st.button(i18n.t("results.preview_make")):
            try:
                png = CONFIG_DIR / "_preview.png"
                desc = quicklook.make_png(str(pick), str(png))
                st.image(str(png), caption=desc, width="stretch")
            except Exception as exc:
                st.caption(i18n.t("process.preview_unavailable", exc=exc))


# ------------------------------------------------------------------ history tab
def tab_history() -> None:
    rows = job_runner.read_history()
    if not rows:
        st.info(i18n.t("history.empty"))
        return
    cols = ["when", "input", "sensor", "format", "duration_s", "result", "error", "version"]
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


def render_footer() -> None:
    st.markdown(
        f"<div class='polymer-foot'>{i18n.t('app.footer')}</div>",
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------- main
def main() -> None:
    pick_language()
    if not licence_gate():
        return
    job_runner.poll()  # keep job state fresh regardless of the active tab
    sidebar_status()

    st.markdown(
        f"<div class='polymer-head'>{_LOGO_SVG}<h1>Polymer</h1></div>",
        unsafe_allow_html=True,
    )
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

    render_footer()


if __name__ == "__main__":
    main()
