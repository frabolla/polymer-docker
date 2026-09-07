"""
Interfaccia grafica per Polymer (correzione atmosferica del colore dell'oceano).

Si apre nel browser su http://localhost:8501 quando il container e' in esecuzione.
Nessun comando da digitare: tutti i parametri si impostano da qui.
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
import setup_status as status
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
JOBS_LOG = OUTPUT_DIR / "_jobs.log"
JOB_TMP = CONFIG_DIR / "_job.json"

st.set_page_config(page_title="Polymer", page_icon="🌊", layout="wide")


# --------------------------------------------------------------------------- util
def stream_command(cmd: list[str], env: dict | None = None) -> int:
    """Esegue `cmd`, riversa stdout/stderr in un box a schermo, ritorna l'exit code."""
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


def append_job_log(entry: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with JOBS_LOG.open("a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_job_log() -> list[dict]:
    if not JOBS_LOG.exists():
        return []
    out = []
    for ln in JOBS_LOG.read_text().splitlines():
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out[::-1]


# ------------------------------------------------------------------ gate: licenza
def licence_gate() -> bool:
    if LICENCE_FLAG.exists():
        return True
    st.title("🌊 Polymer — Termini d'uso")
    st.warning(
        "Prima di usare Polymer devi accettare i Termini d'uso di HYGEOS. "
        "In sintesi: uso gratuito **solo per scopi non commerciali** e **non ridistribuibile**."
    )
    if LICENCE_FILE.exists():
        st.text_area("LICENCE.TXT", LICENCE_FILE.read_text(), height=320)
    agree = st.checkbox("Ho letto e accetto i Termini d'uso di Polymer")
    if st.button("Continua", disabled=not agree, type="primary"):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        LICENCE_FLAG.write_text(datetime.now().isoformat())
        st.rerun()
    return False


# ---------------------------------------------------------------- sidebar / stato
def sidebar_status() -> None:
    st.sidebar.header("Stato configurazione")

    ok_cy = status.cython_modules_ok()
    st.sidebar.write(("✅" if ok_cy else "❌") + " Moduli di calcolo compilati")

    ok_aux = status.auxdata_present()
    size = status.auxdata_size_mb()
    st.sidebar.write(
        ("✅" if ok_aux else "⬇️") + f" Dati ausiliari statici ({size:.0f} MB)"
    )

    cs = cred.status()
    st.sidebar.write(
        ("✅" if cs["earthdata"] else "➖")
        + " NASA Earthdata"
        + (f" ({cs['earthdata_login']})" if cs["earthdata"] else "")
    )
    st.sidebar.write(("✅" if cs["cds"] else "➖") + " Copernicus CDS / ERA5")

    st.sidebar.divider()
    if not ok_aux:
        st.sidebar.info("Scarica i dati ausiliari dalla scheda **Configurazione**.")
    st.sidebar.caption(
        "Cartelle sull'host:\n\n"
        "`data/input` → prodotti Level-1\n\n"
        "`data/output` → risultati\n\n"
        "`data/config` → credenziali"
    )


# --------------------------------------------------------- scheda: configurazione
def tab_config() -> None:
    st.subheader("Dati ausiliari statici")
    st.write(
        "Polymer ha bisogno di alcune tabelle di riferimento (circa 1 GB, incluso "
        "`LUT.hdf`). Si scaricano **una sola volta** nella cartella `data/auxdata`."
    )
    if status.auxdata_present():
        st.success(f"Dati ausiliari presenti ({status.auxdata_size_mb():.0f} MB).")
    if st.button("Scarica / aggiorna dati ausiliari", type="primary"):
        rc = stream_command([sys.executable, "-m", "polymer.get_auxdata"])
        if rc == 0:
            st.success("Download completato.")
        else:
            st.error(f"Download fallito (codice {rc}). Controlla la connessione e riprova.")

    st.divider()
    st.subheader("Credenziali dati meteo (facoltative)")
    st.write(
        "Servono per scaricare **al volo** ozono, vento e pressione. Senza credenziali "
        "Polymer usa comunque delle climatologie interne."
    )

    src = st.radio(
        "Fonte dei dati meteo",
        options=list(ANCILLARY_SOURCES.keys()),
        format_func=lambda k: ANCILLARY_SOURCES[k],
        horizontal=False,
        key="anc_source_config",
    )

    if src == "NASA":
        ed = cred.read_earthdata()
        with st.form("form_nasa"):
            login = st.text_input("Nome utente Earthdata", value=ed.get("login", ""))
            pw = st.text_input("Password Earthdata", type="password")
            c1, c2 = st.columns(2)
            save = c1.form_submit_button("Salva credenziali NASA", type="primary")
            clear = c2.form_submit_button("Rimuovi")
        if save:
            if login and pw:
                cred.write_earthdata(login, pw)
                st.success("Credenziali NASA salvate in data/config/.netrc")
                st.rerun()
            else:
                st.error("Inserisci sia nome utente sia password.")
        if clear:
            cred.clear_earthdata()
            st.info("Credenziali NASA rimosse.")
            st.rerun()
        st.caption(
            "Registrazione gratuita: https://urs.earthdata.nasa.gov/users/new — "
            "ricorda di autorizzare l'applicazione «NASA GESDISC DATA ARCHIVE»."
        )

    elif src == "ERA5":
        cds = cred.read_cds()
        with st.form("form_cds"):
            key = st.text_input(
                "CDS API key", value=cds.get("key", ""),
                help="La trovi nella tua pagina profilo su cds.climate.copernicus.eu",
            )
            c1, c2 = st.columns(2)
            save = c1.form_submit_button("Salva API key CDS", type="primary")
            clear = c2.form_submit_button("Rimuovi")
        if save:
            if key.strip():
                cred.write_cds(key.strip())
                st.success("API key salvata in data/config/.cdsapirc")
                st.rerun()
            else:
                st.error("Inserisci la API key.")
        if clear:
            cred.clear_cds()
            st.info("API key CDS rimossa.")
            st.rerun()
        st.caption("Registrazione gratuita: https://cds.climate.copernicus.eu/user/register")

    else:
        st.info("Nessuna credenziale richiesta per questa scelta.")


# ------------------------------------------------------- costruzione config job
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
    # Passa i parametri di ritaglio solo se l'utente li ha cambiati dai default
    # (0 / -1): alcune classi Level1 non accettano scol/ecol.
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
    """Converte righe 'chiave = valore' in un dizionario (valori come JSON se possibile)."""
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


def run_job(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    JOB_TMP.write_text(json.dumps(cfg, indent=2))
    st.write(f"**Elaborazione di:** `{cfg['input']}`")
    t0 = time.time()
    rc = stream_command([sys.executable, str(APP_DIR / "polymer_job.py"), "--config", str(JOB_TMP)])
    dt = time.time() - t0
    entry = {
        "quando": datetime.now().isoformat(timespec="seconds"),
        "input": cfg["input"],
        "sensore": cfg["sensor"],
        "formato": cfg["fmt"],
        "durata_s": round(dt, 1),
        "esito": "ok" if rc == 0 else f"errore ({rc})",
    }
    append_job_log(entry)

    if rc != 0:
        st.error(f"Elaborazione fallita (codice {rc}). Vedi il log qui sopra.")
        return
    st.success(f"Completato in {dt:.0f} s. Risultati in `data/output/`.")

    newest = _newest_output()
    if newest is not None:
        st.write(f"**File prodotto:** `{newest.name}` ({newest.stat().st_size/1e6:.1f} MB)")
        try:
            import quicklook

            png = CONFIG_DIR / "_preview.png"
            desc = quicklook.make_png(str(newest), str(png))
            st.image(str(png), caption=desc, use_container_width=True)
        except Exception as exc:  # anteprima non critica
            st.caption(f"(Anteprima non disponibile: {exc})")


def _newest_output() -> Path | None:
    if not OUTPUT_DIR.exists():
        return None
    files = [
        p for p in OUTPUT_DIR.iterdir()
        if p.is_file() and p.suffix in (".nc", ".hdf") and not p.name.startswith("_")
    ]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


# ---------------------------------------------------------- scheda: elaborazione
def tab_process() -> None:
    if not status.overall_ready():
        st.warning(
            "Configurazione incompleta: servono i moduli compilati e i dati ausiliari. "
            "Apri la scheda **Configurazione**."
        )

    products = status.list_input_products()
    if not products:
        st.info(
            "Nessun prodotto in `data/input/`. Copia lì i tuoi prodotti Level-1 "
            "(cartelle `.SEN3`, `.SAFE`, file `.N1`, `.L1C`, `.he5` …) e ricarica la pagina."
        )
        return

    col_l, col_r = st.columns([2, 1])
    with col_l:
        selected = st.multiselect(
            "Prodotti Level-1 da elaborare",
            products,
            default=products[:1],
            help="Selezionane più di uno per l'elaborazione in lotto.",
        )
    with col_r:
        sensor = st.selectbox("Sensore", SENSORS, index=0)
        fmt = st.selectbox("Formato di output", OUTPUT_FORMATS, index=0)

    resolution = "60"
    if sensor == "MSI":
        resolution = st.selectbox("Risoluzione MSI (m)", ["10", "20", "60"], index=2)
    if sensor in NEEDS_EXPLICIT_SENSOR:
        st.caption(
            f"Il sensore {sensor} non è rilevabile automaticamente: selezionalo qui esplicitamente."
        )

    ancillary = st.selectbox(
        "Dati meteo ausiliari",
        list(ANCILLARY_SOURCES.keys()),
        format_func=lambda k: ANCILLARY_SOURCES[k],
        index=0,
    )

    st.markdown("**Parametri comuni**")
    common_vals: dict = {}
    cols = st.columns(3)
    for i, p in enumerate(COMMON_PARAMS):
        with cols[i % 3]:
            common_vals[p["name"]] = st.number_input(
                p["label"], value=int(p["default"]), step=1, help=p["help"], key=f"cp_{p['name']}"
            )
    c1, c2, c3 = st.columns(3)
    common_vals["water_model"] = c1.selectbox(
        "Modello dell'acqua", list(WATER_MODELS.keys()),
        format_func=lambda k: WATER_MODELS[k], index=0,
    )
    common_vals["normalize"] = c2.selectbox(
        "Normalizzazione", list(NORMALIZE.keys()),
        format_func=lambda k: NORMALIZE[k], index=0,
    )
    common_vals["force_initialization"] = c3.checkbox("force_initialization", value=False)

    with st.expander("Parametri avanzati (una coppia « nome = valore » per riga)"):
        st.caption(
            "Passati direttamente a `run_atm_corr`. Riferimento: `polymer/params.py`. "
            "Esempi:\n\n`Rprime_consistency = false`\n\n`calib = null`"
        )
        advanced_text = st.text_area("Avanzati", value="", height=140, label_visibility="collapsed")

    output_name = ""
    if len(selected) == 1:
        output_name = st.text_input(
            "Nome file di output (facoltativo)", value="",
            help="Vuoto = nome automatico basato sul prodotto di input.",
        )

    if st.button("▶ Avvia Polymer", type="primary", disabled=not selected):
        advanced = parse_advanced(advanced_text)
        progress = st.progress(0.0)
        for idx, name in enumerate(selected):
            st.divider()
            st.markdown(f"### {idx + 1}/{len(selected)} — {name}")
            cfg = build_job_config(
                input_path=str(Path("/data/input") / name),
                sensor=sensor,
                fmt=fmt,
                resolution=resolution,
                ancillary=ancillary,
                output_name=output_name if len(selected) == 1 else "",
                common_vals=common_vals,
                advanced=advanced,
            )
            run_job(cfg)
            progress.progress((idx + 1) / len(selected))
        st.balloons()


# -------------------------------------------------------------- scheda: cronologia
def tab_history() -> None:
    rows = read_job_log()
    if not rows:
        st.info("Nessuna elaborazione registrata finora.")
        return
    st.dataframe(rows, use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------------- main
def main() -> None:
    if not licence_gate():
        return
    sidebar_status()
    st.title("🌊 Polymer")
    st.caption("Correzione atmosferica del colore dell'oceano — HYGEOS")

    t_proc, t_conf, t_hist = st.tabs(["Elaborazione", "Configurazione", "Cronologia"])
    with t_proc:
        tab_process()
    with t_conf:
        tab_config()
    with t_hist:
        tab_history()


if __name__ == "__main__":
    main()
