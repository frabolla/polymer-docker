"""
Minimal translation layer for the Polymer web interface.

English is the primary language; Italian is available from a selector in the
sidebar. The chosen language is remembered in /data/config/.polymer_lang.

Usage:
    import i18n
    i18n.set_lang("it")
    i18n.t("licence.continue")
    i18n.t("process.file_produced", name="out.nc", size=12.3)
"""
from __future__ import annotations

import os
from pathlib import Path

LANGUAGES = {"en": "English", "it": "Italiano"}
DEFAULT_LANG = "en"

_LANG_FILE = Path(os.environ.get("HOME", "/data/config")) / ".polymer_lang"
_current = DEFAULT_LANG


def load_saved_lang() -> str:
    try:
        val = _LANG_FILE.read_text().strip()
        if val in LANGUAGES:
            return val
    except Exception:
        pass
    return DEFAULT_LANG


def save_lang(lang: str) -> None:
    if lang not in LANGUAGES:
        return
    try:
        _LANG_FILE.parent.mkdir(parents=True, exist_ok=True)
        _LANG_FILE.write_text(lang)
    except Exception:
        pass


def set_lang(lang: str) -> None:
    global _current
    _current = lang if lang in LANGUAGES else DEFAULT_LANG


def get_lang() -> str:
    return _current


def t(key: str, **fmt) -> str:
    """Translate `key` into the current language, formatting with `fmt` if given."""
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_current) or entry.get("en") or key
    if fmt:
        try:
            return text.format(**fmt)
        except Exception:
            return text
    return text


# --------------------------------------------------------------------------- data
# Every user-facing string in the interface. Keep the two languages in sync.
_STRINGS: dict[str, dict[str, str]] = {
    # -- generic / layout
    "app.caption": {
        "en": "Atmospheric correction of ocean colour — HYGEOS",
        "it": "Correzione atmosferica del colore dell'oceano — HYGEOS",
    },
    "sidebar.language": {"en": "Language", "it": "Lingua"},
    "tab.process": {"en": "Processing", "it": "Elaborazione"},
    "tab.config": {"en": "Setup", "it": "Configurazione"},
    "tab.history": {"en": "History", "it": "Cronologia"},

    # -- licence gate
    "licence.title": {"en": "Polymer — Terms of use", "it": "Polymer — Termini d'uso"},
    "licence.warning": {
        "en": "Before using Polymer you must accept HYGEOS' Terms of use. In short: "
              "free for **non-commercial purposes only** and **not redistributable**.",
        "it": "Prima di usare Polymer devi accettare i Termini d'uso di HYGEOS. In "
              "sintesi: uso gratuito **solo per scopi non commerciali** e **non "
              "ridistribuibile**.",
    },
    "licence.checkbox": {
        "en": "I have read and accept Polymer's Terms of use",
        "it": "Ho letto e accetto i Termini d'uso di Polymer",
    },
    "licence.continue": {"en": "Continue", "it": "Continua"},

    # -- sidebar status
    "status.header": {"en": "Setup status", "it": "Stato configurazione"},
    "status.modules": {"en": "Compute modules compiled", "it": "Moduli di calcolo compilati"},
    "status.auxdata": {
        "en": "Static auxiliary data ({size:.0f} MB)",
        "it": "Dati ausiliari statici ({size:.0f} MB)",
    },
    "status.earthdata": {"en": "NASA Earthdata", "it": "NASA Earthdata"},
    "status.cds": {"en": "Copernicus CDS / ERA5", "it": "Copernicus CDS / ERA5"},
    "status.need_auxdata": {
        "en": "Download the auxiliary data from the **Setup** tab.",
        "it": "Scarica i dati ausiliari dalla scheda **Configurazione**.",
    },
    "status.folders": {
        "en": "Folders on the host:\n\n`data/input` → Level-1 products\n\n"
              "`data/output` → results\n\n`data/config` → credentials",
        "it": "Cartelle sull'host:\n\n`data/input` → prodotti Level-1\n\n"
              "`data/output` → risultati\n\n`data/config` → credenziali",
    },

    # -- setup tab: auxiliary data
    "config.aux_header": {"en": "Static auxiliary data", "it": "Dati ausiliari statici"},
    "config.aux_text": {
        "en": "Polymer needs some reference tables (about 1 GB, including `LUT.hdf`). "
              "They are downloaded **once** into the `data/auxdata` folder.",
        "it": "Polymer ha bisogno di alcune tabelle di riferimento (circa 1 GB, incluso "
              "`LUT.hdf`). Si scaricano **una sola volta** nella cartella `data/auxdata`.",
    },
    "config.aux_present": {
        "en": "Auxiliary data present ({size:.0f} MB).",
        "it": "Dati ausiliari presenti ({size:.0f} MB).",
    },
    "config.aux_button": {
        "en": "Download / update auxiliary data",
        "it": "Scarica / aggiorna dati ausiliari",
    },
    "config.aux_ok": {"en": "Download complete.", "it": "Download completato."},
    "config.aux_fail": {
        "en": "Download failed (code {rc}). Check your connection and try again.",
        "it": "Download fallito (codice {rc}). Controlla la connessione e riprova.",
    },

    # -- setup tab: credentials
    "config.cred_header": {
        "en": "Meteorological data credentials (optional)",
        "it": "Credenziali dati meteo (facoltative)",
    },
    "config.cred_text": {
        "en": "Used to download ozone, wind and pressure **on the fly**. Without "
              "credentials Polymer falls back to built-in climatologies.",
        "it": "Servono per scaricare **al volo** ozono, vento e pressione. Senza "
              "credenziali Polymer usa comunque delle climatologie interne.",
    },
    "config.cred_source": {"en": "Meteorological data source", "it": "Fonte dei dati meteo"},
    "config.nasa_user": {"en": "Earthdata username", "it": "Nome utente Earthdata"},
    "config.nasa_pass": {"en": "Earthdata password", "it": "Password Earthdata"},
    "config.nasa_save": {"en": "Save NASA credentials", "it": "Salva credenziali NASA"},
    "config.remove": {"en": "Remove", "it": "Rimuovi"},
    "config.nasa_saved": {
        "en": "NASA credentials saved to data/config/.netrc",
        "it": "Credenziali NASA salvate in data/config/.netrc",
    },
    "config.nasa_need_both": {
        "en": "Enter both username and password.",
        "it": "Inserisci sia nome utente sia password.",
    },
    "config.nasa_removed": {"en": "NASA credentials removed.", "it": "Credenziali NASA rimosse."},
    "config.nasa_hint": {
        "en": "Free registration: https://urs.earthdata.nasa.gov/users/new — remember "
              "to authorize the «NASA GESDISC DATA ARCHIVE» application.",
        "it": "Registrazione gratuita: https://urs.earthdata.nasa.gov/users/new — "
              "ricorda di autorizzare l'applicazione «NASA GESDISC DATA ARCHIVE».",
    },
    "config.cds_key": {"en": "CDS API key", "it": "CDS API key"},
    "config.cds_key_help": {
        "en": "Found on your profile page at cds.climate.copernicus.eu",
        "it": "La trovi nella tua pagina profilo su cds.climate.copernicus.eu",
    },
    "config.cds_save": {"en": "Save CDS API key", "it": "Salva API key CDS"},
    "config.cds_saved": {
        "en": "API key saved to data/config/.cdsapirc",
        "it": "API key salvata in data/config/.cdsapirc",
    },
    "config.cds_need_key": {"en": "Enter the API key.", "it": "Inserisci la API key."},
    "config.cds_removed": {"en": "CDS API key removed.", "it": "API key CDS rimossa."},
    "config.cds_hint": {
        "en": "Free registration: https://cds.climate.copernicus.eu/user/register",
        "it": "Registrazione gratuita: https://cds.climate.copernicus.eu/user/register",
    },
    "config.cred_none": {
        "en": "No credentials required for this choice.",
        "it": "Nessuna credenziale richiesta per questa scelta.",
    },

    # -- processing tab
    "process.incomplete": {
        "en": "Setup incomplete: compiled modules and auxiliary data are required. "
              "Open the **Setup** tab.",
        "it": "Configurazione incompleta: servono i moduli compilati e i dati "
              "ausiliari. Apri la scheda **Configurazione**.",
    },
    "process.no_products": {
        "en": "No products in `data/input/`. Copy your Level-1 products there "
              "(`.SEN3`, `.SAFE` folders, `.N1`, `.L1C`, `.he5` files …) and reload "
              "the page.",
        "it": "Nessun prodotto in `data/input/`. Copia lì i tuoi prodotti Level-1 "
              "(cartelle `.SEN3`, `.SAFE`, file `.N1`, `.L1C`, `.he5` …) e ricarica "
              "la pagina.",
    },
    "process.products": {"en": "Level-1 products to process", "it": "Prodotti Level-1 da elaborare"},
    "process.products_help": {
        "en": "Select more than one for batch processing.",
        "it": "Selezionane più di uno per l'elaborazione in lotto.",
    },
    "process.sensor": {"en": "Sensor", "it": "Sensore"},
    "process.fmt": {"en": "Output format", "it": "Formato di output"},
    "process.msi_res": {"en": "MSI resolution (m)", "it": "Risoluzione MSI (m)"},
    "process.explicit_sensor": {
        "en": "The {sensor} sensor is not auto-detected: select it explicitly here.",
        "it": "Il sensore {sensor} non è rilevabile automaticamente: selezionalo qui "
              "esplicitamente.",
    },
    "process.ancillary": {"en": "Auxiliary meteorological data", "it": "Dati meteo ausiliari"},
    "process.common_params": {"en": "**Common parameters**", "it": "**Parametri comuni**"},
    "process.water_model": {"en": "Water model", "it": "Modello dell'acqua"},
    "process.normalize": {"en": "Normalization", "it": "Normalizzazione"},
    "process.force_init": {"en": "force_initialization", "it": "force_initialization"},
    "process.advanced": {
        "en": "Advanced parameters (one « name = value » pair per line)",
        "it": "Parametri avanzati (una coppia « nome = valore » per riga)",
    },
    "process.advanced_help": {
        "en": "Passed straight to `run_atm_corr`. Reference: `polymer/params.py`. "
              "Examples:\n\n`Rprime_consistency = false`\n\n`calib = null`",
        "it": "Passati direttamente a `run_atm_corr`. Riferimento: `polymer/params.py`. "
              "Esempi:\n\n`Rprime_consistency = false`\n\n`calib = null`",
    },
    "process.output_name": {"en": "Output file name (optional)", "it": "Nome file di output (facoltativo)"},
    "process.output_name_help": {
        "en": "Empty = automatic name based on the input product.",
        "it": "Vuoto = nome automatico basato sul prodotto di input.",
    },
    "process.run": {"en": "▶ Run Polymer", "it": "▶ Avvia Polymer"},
    "process.processing_of": {"en": "**Processing:** `{input}`", "it": "**Elaborazione di:** `{input}`"},
    "process.failed": {
        "en": "Processing failed (code {rc}). See the log above.",
        "it": "Elaborazione fallita (codice {rc}). Vedi il log qui sopra.",
    },
    "process.done": {
        "en": "Done in {dt:.0f} s. Results in `data/output/`.",
        "it": "Completato in {dt:.0f} s. Risultati in `data/output/`.",
    },
    "process.file_produced": {
        "en": "**File produced:** `{name}` ({size:.1f} MB)",
        "it": "**File prodotto:** `{name}` ({size:.1f} MB)",
    },
    "process.preview_unavailable": {
        "en": "(Preview unavailable: {exc})",
        "it": "(Anteprima non disponibile: {exc})",
    },

    # -- history tab
    "history.empty": {
        "en": "No processing recorded yet.",
        "it": "Nessuna elaborazione registrata finora.",
    },
    "history.col.when": {"en": "when", "it": "quando"},
    "history.col.input": {"en": "input", "it": "input"},
    "history.col.sensor": {"en": "sensor", "it": "sensore"},
    "history.col.format": {"en": "format", "it": "formato"},
    "history.col.duration_s": {"en": "duration (s)", "it": "durata (s)"},
    "history.col.result": {"en": "result", "it": "esito"},
    "history.result.ok": {"en": "ok", "it": "ok"},
    "history.result.error": {"en": "error ({rc})", "it": "errore ({rc})"},

    # -- common parameter labels / help (keyed by param name)
    "param.multiprocessing.label": {"en": "Number of CPU cores", "it": "Numero di core CPU"},
    "param.multiprocessing.help": {
        "en": "0 = single core.  -1 = all available cores.  N = N cores.",
        "it": "0 = un solo core.  -1 = tutti i core disponibili.  N = N core.",
    },
    "param.sline.label": {"en": "First row (crop)", "it": "Riga iniziale (ritaglio)"},
    "param.sline.help": {
        "en": "Crop the product: first row to process (0 = from the start).",
        "it": "Ritaglia il prodotto: prima riga da elaborare (0 = dall'inizio).",
    },
    "param.eline.label": {"en": "Last row (crop)", "it": "Riga finale (ritaglio)"},
    "param.eline.help": {
        "en": "Last row to process (-1 = to the end).",
        "it": "Ultima riga da elaborare (-1 = fino alla fine).",
    },
    "param.scol.label": {"en": "First column (crop)", "it": "Colonna iniziale (ritaglio)"},
    "param.scol.help": {
        "en": "First column to process (0 = from the start). Ignored by some sensors.",
        "it": "Prima colonna da elaborare (0 = dall'inizio). Ignorato da alcuni sensori.",
    },
    "param.ecol.label": {"en": "Last column (crop)", "it": "Colonna finale (ritaglio)"},
    "param.ecol.help": {
        "en": "Last column to process (-1 = to the end).",
        "it": "Ultima colonna da elaborare (-1 = fino alla fine).",
    },

    # -- water model options
    "watermodel.PR05": {
        "en": "Park & Ruddick 2005 (default, recommended)",
        "it": "Park & Ruddick 2005 (predefinito, consigliato)",
    },
    "watermodel.MM01": {"en": "Morel & Maritorena 2001", "it": "Morel & Maritorena 2001"},
    "watermodel.MM01_FOQ": {
        "en": "Morel & Maritorena 2001 with directional f/Q",
        "it": "Morel & Maritorena 2001 con f/Q direzionale",
    },

    # -- normalization options
    "normalize.0": {"en": "No normalization", "it": "Nessuna normalizzazione"},
    "normalize.1": {
        "en": "Normalize water reflectance at nadir",
        "it": "Normalizza la riflettanza dell'acqua al nadir",
    },
    "normalize.2": {
        "en": "Wavelength normalization (MERIS/OLCI)",
        "it": "Normalizzazione in lunghezza d'onda (MERIS/OLCI)",
    },
    "normalize.3": {"en": "Both (nadir + wavelength)", "it": "Entrambe (nadir + lunghezza d'onda)"},

    # -- ancillary source options
    "ancillary.auto": {
        "en": "Automatic (use NASA if credentials are available)",
        "it": "Automatico (usa NASA se disponibili le credenziali)",
    },
    "ancillary.NASA": {
        "en": "NASA Earthdata (ozone, wind, pressure)",
        "it": "NASA Earthdata (ozono, vento, pressione)",
    },
    "ancillary.ERA5": {"en": "Copernicus ERA5 / CDS", "it": "Copernicus ERA5 / CDS"},
    "ancillary.none": {
        "en": "None (use built-in climatologies)",
        "it": "Nessuno (usa le climatologie interne)",
    },

    # -- quicklook captions
    "quicklook.rgb": {
        "en": "Water reflectance RGB (665 / 560 / 443 nm)",
        "it": "RGB della riflettanza dell'acqua (665 / 560 / 443 nm)",
    },
    "quicklook.map_chl": {
        "en": "Map of '{name}' (log chlorophyll)",
        "it": "Mappa di '{name}' (log clorofilla)",
    },
    "quicklook.map_var": {"en": "Map of '{name}'", "it": "Mappa di '{name}'"},
}
