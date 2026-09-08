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
        "en": "Atmospheric correction of ocean colour",
        "it": "Correzione atmosferica del colore dell'oceano",
    },
    "app.fork_note": {
        "en": "This tool is a fork of the open-source **Polymer** algorithm by "
              "HYGEOS. Original software: "
              "[github.com/hygeos/polymer](https://github.com/hygeos/polymer).",
        "it": "Questo strumento è un fork dell'algoritmo open-source **Polymer** di "
              "HYGEOS. Software originale: "
              "[github.com/hygeos/polymer](https://github.com/hygeos/polymer).",
    },
    "app.author": {
        "en": "Docker packaging and interface by **Francesco Tarini** "
              "([@frabolla](https://github.com/frabolla)).",
        "it": "Pacchetto Docker e interfaccia realizzati da **Francesco Tarini** "
              "([@frabolla](https://github.com/frabolla)).",
    },
    "app.footer": {
        "en": "Fork of Polymer by HYGEOS. Docker packaging by Francesco Tarini "
              "(@frabolla). Polymer itself is © HYGEOS — see LICENCE.TXT.",
        "it": "Fork di Polymer di HYGEOS. Pacchetto Docker di Francesco Tarini "
              "(@frabolla). Polymer è © HYGEOS — vedi LICENCE.TXT.",
    },
    "check.auxdata": {
        "en": "Auxiliary data downloaded",
        "it": "Dati ausiliari scaricati",
    },
    "check.creds": {
        "en": "Meteorological-data credentials entered",
        "it": "Credenziali dati meteo inserite",
    },
    "check.saved_short": {"en": "saved", "it": "salvata"},
    "sidebar.language": {"en": "Language", "it": "Lingua"},
    "sidebar.version": {"en": "Version {v}", "it": "Versione {v}"},
    "sidebar.freespace": {"en": "Free space: {mb:.0f} MB", "it": "Spazio libero: {mb:.0f} MB"},
    "tab.process": {"en": "Processing", "it": "Elaborazione"},
    "tab.config": {"en": "Setup", "it": "Configurazione"},
    "tab.guide": {"en": "Guide", "it": "Guida"},
    "tab.results": {"en": "Results", "it": "Risultati"},
    "tab.history": {"en": "History", "it": "Cronologia"},

    # -- running job panel
    "run.title": {"en": "Processing in progress", "it": "Elaborazione in corso"},
    "run.batch_pos": {
        "en": "Job {i} of {n} — {q} queued",
        "it": "Job {i} di {n} — {q} in coda",
    },
    "run.processing": {"en": "Current product: {input}", "it": "Prodotto in corso: {input}"},
    "run.blocks": {"en": "{d} / {n} blocks", "it": "{d} / {n} blocchi"},
    "run.blocks_nototal": {"en": "{d} blocks processed", "it": "{d} blocchi elaborati"},
    "run.elapsed": {"en": "Elapsed: {s} s", "it": "Trascorso: {s} s"},
    "run.eta": {"en": "about {s} s left", "it": "circa {s} s rimanenti"},
    "run.cancel": {"en": "Cancel", "it": "Annulla"},
    "run.queued_only": {"en": "{q} job(s) queued.", "it": "{q} job in coda."},
    "run.log": {"en": "Show detailed log", "it": "Mostra log dettagliato"},
    "run.phase_reading": {
        "en": "Reading the input image…", "it": "Lettura dell'immagine di input…",
    },
    "run.phase_meteo": {
        "en": "Downloading meteorological data (ozone / wind / pressure)…",
        "it": "Scaricamento dati meteo (ozono / vento / pressione)…",
    },
    "run.phase_starting": {
        "en": "Preparing the output file…", "it": "Preparazione del file di output…",
    },
    "run.phase_processing": {
        "en": "Applying the atmospheric correction…",
        "it": "Applicazione della correzione atmosferica…",
    },
    "run.phase_download": {
        "en": "Downloading…", "it": "Scaricamento in corso…",
    },
    "done.title": {
        "en": "Atmospheric correction completed — {n} file(s) ready.",
        "it": "Correzione atmosferica completata — {n} file pronti.",
    },
    "done.partial": {
        "en": "Finished: {ok} ok, {fail} failed.",
        "it": "Terminato: {ok} riusciti, {fail} falliti.",
    },
    "done.failed": {
        "en": "The correction failed ({n} file(s)). See the message below.",
        "it": "La correzione è fallita ({n} file). Vedi il messaggio qui sotto.",
    },
    "done.file": {"en": "Output: {name}", "it": "Output: {name}"},
    "done.download": {"en": "Download", "it": "Scarica"},
    "done.results_tab": {
        "en": "Open in the Results tab", "it": "Apri nella scheda Risultati",
    },

    # -- batch summary
    "batch.title": {"en": "Last run", "it": "Ultima elaborazione"},
    "batch.summary": {
        "en": "{ok} succeeded, {fail} failed out of {n}.",
        "it": "{ok} riuscite, {fail} fallite su {n}.",
    },
    "batch.dismiss": {"en": "Clear", "it": "Nascondi"},
    "batch.rerun_failed": {"en": "Re-run the {n} failed", "it": "Ripeti i {n} falliti"},

    # -- upload
    "upload.header": {"en": "Upload a product", "it": "Carica un prodotto"},
    "upload.label": {
        "en": "Drop a .zip (for .SEN3 / .SAFE folder products) or a single-file "
              "product (.nc, .he5, .N1, .L1C, .csv)",
        "it": "Trascina uno .zip (per prodotti a cartella .SEN3 / .SAFE) o un "
              "prodotto a file singolo (.nc, .he5, .N1, .L1C, .csv)",
    },
    "upload.save": {"en": "Save to data/input", "it": "Salva in data/input"},

    # -- results tab
    "results.none": {
        "en": "No results yet in `data/output/`. Run a processing first.",
        "it": "Ancora nessun risultato in `data/output/`. Esegui prima "
              "un'elaborazione.",
    },
    "results.pick": {"en": "Result file", "it": "File risultato"},
    "results.info": {"en": "{name} — {size:.1f} MB — {when}", "it": "{name} — {size:.1f} MB — {when}"},
    "results.variable": {"en": "Variable to preview", "it": "Variabile da visualizzare"},
    "results.auto": {"en": "auto (RGB / chlorophyll)", "it": "auto (RGB / clorofilla)"},
    "results.download": {"en": "Download this file", "it": "Scarica questo file"},
    "results.too_big": {
        "en": "File is {size:.0f} MB — copy it from the `data/output` folder instead.",
        "it": "File di {size:.0f} MB — copialo dalla cartella `data/output`.",
    },
    "results.preview_header": {
        "en": "Quick visual check (optional)", "it": "Controllo visivo rapido (facoltativo)",
    },
    "results.preview_hint": {
        "en": "A small RGB preview of the water reflectance, only to confirm the "
              "correction ran. Polymer's real output is the file above.",
        "it": "Una piccola anteprima RGB della riflettanza dell'acqua, solo per "
              "confermare che la correzione è stata eseguita. L'output vero di "
              "Polymer è il file qui sopra.",
    },
    "results.preview_make": {"en": "Generate preview", "it": "Genera anteprima"},

    # -- working folders panel
    "folders.header": {"en": "Working folders on your computer", "it": "Cartelle di lavoro sul tuo computer"},
    "folders.open_hint": {
        "en": "Copy a path and paste it into Finder (macOS) or File Explorer "
              "(Windows) to open the folder.",
        "it": "Copia un percorso e incollalo in Finder (macOS) o Esplora file "
              "(Windows) per aprire la cartella.",
    },
    "folders.input": {"en": "Input — put your Level-1 products here", "it": "Input — metti qui i prodotti Level-1"},
    "folders.output": {"en": "Output — corrected images appear here", "it": "Output — qui compaiono le immagini corrette"},
    "folders.config": {"en": "Config — saved credentials and settings", "it": "Config — credenziali e impostazioni salvate"},
    "folders.in_container": {"en": "path inside the container", "it": "percorso dentro il container"},
    "folders.container_note": {
        "en": "The container was started by hand, so the exact host paths are "
              "unknown. They are the `data/input`, `data/output` and `data/config` "
              "folders next to the launcher.",
        "it": "Il container è stato avviato manualmente, quindi i percorsi esatti "
              "sul computer non sono noti. Sono le cartelle `data/input`, "
              "`data/output` e `data/config` accanto al launcher.",
    },
    "folders.change_button": {
        "en": "Change the input / output folders…",
        "it": "Cambia le cartelle input / output…",
    },
    "folders.change_title": {
        "en": "Choose the input and output folders",
        "it": "Scegli le cartelle di input e output",
    },
    "folders.change_hint": {
        "en": "Type or paste a full folder path from this computer (e.g. an "
              "external drive). The **config** folder cannot be moved. The change "
              "takes effect the next time you start Polymer with the launcher.",
        "it": "Digita o incolla il percorso completo di una cartella di questo "
              "computer (es. un disco esterno). La cartella **config** non si può "
              "spostare. La modifica ha effetto al prossimo avvio di Polymer dal "
              "launcher.",
    },
    "folders.save": {"en": "Save", "it": "Salva"},
    "folders.saved_restart": {
        "en": "Saved. Close Polymer and start it again with the launcher to use "
              "the new folders.",
        "it": "Salvato. Chiudi Polymer e riavvialo dal launcher per usare le "
              "nuove cartelle.",
    },
    "folders.reset": {"en": "Back to default", "it": "Torna ai valori predefiniti"},
    "folders.reset_done": {
        "en": "Reset. Restart Polymer to use the default folders.",
        "it": "Ripristinato. Riavvia Polymer per usare le cartelle predefinite.",
    },
    "folders.custom_active": {
        "en": "Custom input/output folders are set (active after the next start).",
        "it": "Sono impostate cartelle input/output personalizzate (attive dal "
              "prossimo avvio).",
    },
    "firstrun.title": {
        "en": "Set up Polymer — one time", "it": "Configura Polymer — una volta sola",
    },
    "firstrun.intro": {
        "en": "Two quick steps before your first processing. Once both are done "
              "this page is replaced by the working interface, and **Processing** "
              "becomes the main tab. What you enter here is saved and reused on "
              "every later start.",
        "it": "Due passaggi rapidi prima della prima elaborazione. Completati "
              "entrambi, questa pagina lascia il posto all'interfaccia di lavoro "
              "e **Elaborazione** diventa la scheda principale. Ciò che inserisci "
              "qui viene salvato e riutilizzato a ogni avvio successivo.",
    },

    # -- in-app guide
    "guide.intro": {
        "en": "Polymer runs entirely on your computer, inside a Docker container. "
              "You drive it from this page; there is nothing to type on a command "
              "line.",
        "it": "Polymer gira interamente sul tuo computer, dentro un container "
              "Docker. Lo comandi da questa pagina; non c'è nulla da digitare a "
              "riga di comando.",
    },
    "guide.first_header": {"en": "First time you start it", "it": "La prima volta che lo avvii"},
    "guide.first_body": {
        "en": "1. **Accept the Terms of use** (done — this is the first page).\n"
              "2. Open the **Setup** tab and click **Download / update auxiliary "
              "data**. This fetches about 1 GB of reference tables and is needed "
              "only once.\n"
              "3. *(Optional)* In **Setup**, enter a **NASA Earthdata** or "
              "**Copernicus CDS** account to let Polymer download weather data "
              "automatically. Without it, built-in climatologies are used.\n"
              "4. Put your **Level-1** products into the `data/input` folder next "
              "to the project, then reload this page.\n"
              "5. Open **Processing**, pick a product and a sensor (`auto` is "
              "usually right), then click **Run Polymer**.\n"
              "6. Results are written to the `data/output` folder; a preview is "
              "shown here.",
        "it": "1. **Accetta i Termini d'uso** (fatto — è questa prima pagina).\n"
              "2. Apri la scheda **Configurazione** e clicca **Scarica / aggiorna "
              "dati ausiliari**. Scarica circa 1 GB di tabelle di riferimento e "
              "serve una sola volta.\n"
              "3. *(Facoltativo)* In **Configurazione**, inserisci un account "
              "**NASA Earthdata** o **Copernicus CDS** per far scaricare a Polymer "
              "i dati meteo in automatico. Senza, si usano le climatologie "
              "interne.\n"
              "4. Metti i tuoi prodotti **Level-1** nella cartella `data/input` "
              "accanto al progetto, poi ricarica questa pagina.\n"
              "5. Apri **Elaborazione**, scegli un prodotto e un sensore (`auto` "
              "di solito va bene), poi clicca **Avvia Polymer**.\n"
              "6. I risultati vengono scritti nella cartella `data/output`; qui "
              "compare un'anteprima.",
    },
    "guide.update_header": {
        "en": "After an update (no full rebuild needed)",
        "it": "Dopo un aggiornamento (senza ricostruire tutto)",
    },
    "guide.update_body": {
        "en": "When a new version of this project is released, you do **not** "
              "rebuild the container from scratch:\n\n"
              "1. Stop the container (Docker Desktop → Containers → Stop), or close "
              "it.\n"
              "2. Download the new version (new ZIP from GitHub, or `git pull`) "
              "over the project folder, keeping your `data/` folder.\n"
              "3. Start it again with the usual launcher. Docker rebuilds **only "
              "the changed layers** — usually under a minute — because the heavy "
              "steps (scientific libraries, compiled modules) are cached.\n\n"
              "Your downloaded auxiliary data, credentials, language and history "
              "all live in `data/` and are kept across updates. You only need to "
              "download the auxiliary data again if this page says it is missing.",
        "it": "Quando esce una nuova versione di questo progetto **non** si "
              "ricostruisce il container da zero:\n\n"
              "1. Ferma il container (Docker Desktop → Containers → Stop), oppure "
              "chiudilo.\n"
              "2. Scarica la nuova versione (nuovo ZIP da GitHub, o `git pull`) "
              "sopra la cartella del progetto, tenendo la cartella `data/`.\n"
              "3. Riavvialo con il solito launcher. Docker ricostruisce **solo i "
              "livelli cambiati** — di solito meno di un minuto — perché i passi "
              "pesanti (librerie scientifiche, moduli compilati) sono in cache.\n\n"
              "I dati ausiliari scaricati, le credenziali, la lingua e la "
              "cronologia stanno tutti in `data/` e si conservano tra un "
              "aggiornamento e l'altro. Devi riscaricare i dati ausiliari solo se "
              "questa pagina segnala che mancano.",
    },
    "guide.about_header": {"en": "About this tool", "it": "Informazioni su questo strumento"},
    "guide.about_body": {
        "en": "This is a **fork** of the open-source Polymer atmospheric-correction "
              "algorithm by HYGEOS, packaged as a Docker container with this "
              "graphical interface for easier installation.\n\n"
              "- Original software: "
              "[github.com/hygeos/polymer](https://github.com/hygeos/polymer)\n"
              "- Polymer is free for **non-commercial use** and **must not be "
              "redistributed** (see the Terms of use on the first page).\n"
              "- Scientific reference: Steinmetz, Deschamps & Ramon, *Atmospheric "
              "correction in presence of sun glint*, Opt. Express 19 (2011).",
        "it": "Questo è un **fork** dell'algoritmo open-source di correzione "
              "atmosferica Polymer di HYGEOS, impacchettato come container Docker "
              "con questa interfaccia grafica per semplificarne l'installazione.\n\n"
              "- Software originale: "
              "[github.com/hygeos/polymer](https://github.com/hygeos/polymer)\n"
              "- Polymer è gratuito per **uso non commerciale** e **non può essere "
              "ridistribuito** (vedi i Termini d'uso nella prima pagina).\n"
              "- Riferimento scientifico: Steinmetz, Deschamps & Ramon, "
              "*Atmospheric correction in presence of sun glint*, Opt. Express 19 "
              "(2011).",
    },

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
    "licence.steps_header": {
        "en": "How to use this tool, in short",
        "it": "Come si usa questo strumento, in breve",
    },
    "licence.steps_body": {
        "en": "1. Accept the terms below.\n"
              "2. **Setup** tab → download the auxiliary data (once, ~1 GB).\n"
              "3. Put your Level-1 products in the `data/input` folder, reload.\n"
              "4. **Processing** tab → choose the product, click *Run Polymer*.\n"
              "5. Get the results from `data/output`.\n\n"
              "The **Guide** tab has the full steps and what to do after an "
              "update.",
        "it": "1. Accetta i termini qui sotto.\n"
              "2. Scheda **Configurazione** → scarica i dati ausiliari (una volta, "
              "~1 GB).\n"
              "3. Metti i tuoi prodotti Level-1 nella cartella `data/input`, "
              "ricarica.\n"
              "4. Scheda **Elaborazione** → scegli il prodotto, clicca *Avvia "
              "Polymer*.\n"
              "5. Prendi i risultati da `data/output`.\n\n"
              "La scheda **Guida** ha i passaggi completi e cosa fare dopo un "
              "aggiornamento.",
    },

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
    "config.aux_running": {
        "en": "Downloading auxiliary data… ({s} s). It runs in the background — "
              "you can switch tabs; this panel updates on its own.",
        "it": "Download dei dati ausiliari in corso… ({s} s). Procede in "
              "background: puoi cambiare scheda, questo pannello si aggiorna da solo.",
    },
    "config.aux_cancel": {"en": "Cancel download", "it": "Annulla download"},
    "config.aux_cancelled": {"en": "Download cancelled.", "it": "Download annullato."},
    "config.aux_log": {"en": "Download log", "it": "Log del download"},
    "config.aux_dismiss": {"en": "Dismiss", "it": "Chiudi"},
    "config.aux_always_required": {
        "en": "These reference tables (the atmospheric-correction lookup tables) "
              "are **always required**, for every sensor. They are not weather "
              "data and are unrelated to the NASA / Copernicus credentials on the "
              "next step — so this step cannot be skipped.",
        "it": "Queste tabelle di riferimento (le lookup table della correzione "
              "atmosferica) sono **sempre necessarie**, per ogni sensore. Non "
              "sono dati meteo e non c'entrano con le credenziali NASA / "
              "Copernicus del passaggio successivo — quindi non si può saltare.",
    },
    "config.aux_retry": {"en": "Retry the download", "it": "Riprova il download"},
    "config.aux_dns": {
        "en": "The container cannot look up internet addresses (DNS): "
              "`download.hygeos.com` does not resolve. This is a network problem "
              "outside Polymer — usually a **VPN** that must be disconnected, or "
              "a network with its own **DNS server** (set it in "
              "`docker/docker-compose.yml`, the `dns:` lines, then restart with "
              "the launcher). Restarting Docker Desktop (right-click the whale "
              "icon → Restart) also often fixes it.",
        "it": "Il container non riesce a risolvere gli indirizzi internet (DNS): "
              "`download.hygeos.com` non si risolve. È un problema di rete "
              "esterno a Polymer — di solito una **VPN** da disconnettere, o una "
              "rete con un proprio **server DNS** (impostalo in "
              "`docker/docker-compose.yml`, le righe `dns:`, poi riavvia dal "
              "launcher). Anche riavviare Docker Desktop (tasto destro "
              "sull'icona della balena → Restart) spesso risolve.",
    },
    "config.aux_retry_hint": {
        "en": "If it stopped on a \"Timeout on Lockfile\" message, just press "
              "Retry: it clears the leftover lock files and continues where it "
              "left off (already-downloaded files are kept).",
        "it": "Se si è fermato su un messaggio «Timeout on Lockfile», premi "
              "Riprova: cancella i file di lock rimasti e riparte da dove si era "
              "interrotto (i file già scaricati vengono mantenuti).",
    },

    # -- setup tab: credentials
    "config.intro": {
        "en": "Before your first run, set up two things here: **(1)** download the "
              "auxiliary data once, and **(2)** enter the credentials for a "
              "meteorological-data service. What you enter is saved on your "
              "computer (in the `config` folder) and reused automatically every "
              "time you start Polymer — you do not need to type it again.",
        "it": "Prima della prima elaborazione, configura due cose qui: **(1)** "
              "scarica una volta i dati ausiliari e **(2)** inserisci le "
              "credenziali di un servizio di dati meteo. Quello che inserisci "
              "viene salvato sul tuo computer (nella cartella `config`) e "
              "riutilizzato automaticamente a ogni avvio di Polymer — non devi "
              "reinserirlo.",
    },
    "config.cred_header": {
        "en": "Meteorological data credentials",
        "it": "Credenziali dati meteo",
    },
    "config.cred_text": {
        "en": "Used to download ozone, wind and pressure **on the fly**. "
              "Sentinel-2/3 can fall back to built-in climatologies; **PRISMA "
              "cannot** — it needs one of these accounts.",
        "it": "Servono per scaricare **al volo** ozono, vento e pressione. "
              "Sentinel-2/3 possono ripiegare su climatologie interne; **PRISMA "
              "no** — richiede uno di questi account.",
    },
    "config.cred_persist": {
        "en": "Saved in `data/config/` and reused on the next launch. Use "
              "**Remove** to clear one and enter a different account.",
        "it": "Salvate in `data/config/` e riutilizzate al prossimo avvio. Usa "
              "**Rimuovi** per cancellarne una e inserire un altro account.",
    },
    "config.saved_as": {"en": "Currently saved: {who}", "it": "Attualmente salvata: {who}"},
    "config.not_saved": {"en": "Nothing saved yet.", "it": "Ancora nulla di salvato."},
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
    "config.cred_test": {"en": "Verify", "it": "Verifica"},
    "config.cred_test_ok": {
        "en": "Credentials look valid.",
        "it": "Le credenziali sembrano valide.",
    },
    "config.cred_test_bad": {
        "en": "Verification failed: {msg}",
        "it": "Verifica fallita: {msg}",
    },
    "config.cred_test_skip": {
        "en": "Could not verify (no network?): {msg}",
        "it": "Impossibile verificare (rete assente?): {msg}",
    },
    "config.low_disk": {
        "en": "Only {mb:.0f} MB free in `data/`. Free up space before downloading.",
        "it": "Solo {mb:.0f} MB liberi in `data/`. Libera spazio prima di scaricare.",
    },

    # -- processing tab
    "process.incomplete": {
        "en": "Setup incomplete: compiled modules and auxiliary data are required. "
              "Open the **Setup** tab.",
        "it": "Configurazione incompleta: servono i moduli compilati e i dati "
              "ausiliari. Apri la scheda **Configurazione**.",
    },
    "process.checklist_header": {
        "en": "Before you can process: 3 steps", "it": "Prima di elaborare: 3 passaggi",
    },
    "process.checklist_intro": {
        "en": "Do these once. Everything is set on the **Setup** tab and then "
              "remembered for next time.",
        "it": "Da fare una volta sola. Si configura tutto nella scheda "
              "**Configurazione** e poi viene ricordato.",
    },
    "process.go_setup": {
        "en": "Open the **Setup** tab to finish the missing steps.",
        "it": "Apri la scheda **Configurazione** per completare i passaggi mancanti.",
    },
    "process.fmt_help": {
        "en": "HDF is Polymer's native Level-2 format. NetCDF is more portable. "
              "The pixel values are the same.",
        "it": "HDF è il formato Level-2 nativo di Polymer. NetCDF è più portabile. "
              "I valori dei pixel sono identici.",
    },
    "process.ancillary_help": {
        "en": "Where Polymer gets ozone / wind / pressure. Pick it yourself each "
              "run. 'None' uses built-in climatologies (not allowed for PRISMA).",
        "it": "Da dove Polymer prende ozono / vento / pressione. Scegli tu a ogni "
              "elaborazione. 'Nessuna' usa climatologie interne (non per PRISMA).",
    },
    "process.ancillary_choose": {"en": "Choose a source…", "it": "Scegli una fonte…"},
    "process.ancillary_need_choice": {
        "en": "Choose the meteorological-data source above before running.",
        "it": "Scegli la fonte dei dati meteo qui sopra prima di elaborare.",
    },
    "process.ancillary_configured": {
        "en": "Configured in Setup: {srcs}", "it": "Configurate in Configurazione: {srcs}",
    },
    "process.ancillary_none_configured": {
        "en": "No meteo account configured yet — add one on the Setup tab.",
        "it": "Nessun account meteo configurato — aggiungine uno nella scheda Configurazione.",
    },
    "process.landmask": {"en": "Land mask", "it": "Maschera di terra"},
    "process.landmask_help": {
        "en": "Whether land pixels are masked out. 'Built-in' uses the mask "
              "supplied with the product (OLCI/MERIS only). 'None' processes land "
              "too. 'GSW' uses the Global Surface Water dataset (must be present).",
        "it": "Se mascherare i pixel di terra. 'Integrata' usa la maschera fornita "
              "col prodotto (solo OLCI/MERIS). 'Nessuna' elabora anche la terra. "
              "'GSW' usa il dataset Global Surface Water (deve essere presente).",
    },
    "process.landmask_none_builtin": {
        "en": "{sensor} products carry no built-in land mask — this is the same "
              "as 'None'. Use 'GSW' to actually mask land.",
        "it": "I prodotti {sensor} non hanno una maschera di terra integrata — "
              "equivale a 'Nessuna'. Usa 'GSW' per mascherare davvero la terra.",
    },
    "landmask.default": {"en": "Product's built-in mask", "it": "Maschera integrata del prodotto"},
    "landmask.none": {"en": "None — process land too", "it": "Nessuna — elabora anche la terra"},
    "landmask.gsw": {"en": "Global Surface Water dataset", "it": "Dataset Global Surface Water"},
    "fmt.hdf4": {"en": "HDF (.hdf) — recommended", "it": "HDF (.hdf) — consigliato"},
    "fmt.netcdf4": {"en": "NetCDF (.nc)", "it": "NetCDF (.nc)"},
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
    "process.detected": {
        "en": "Auto-detected sensor: **{sensor}**",
        "it": "Sensore rilevato: **{sensor}**",
    },
    "process.detect_fail": {
        "en": "Could not auto-detect the sensor from the file name — pick one below.",
        "it": "Impossibile rilevare il sensore dal nome file — scegline uno qui sotto.",
    },
    "process.low_disk": {
        "en": "Only {mb:.0f} MB free in `data/`. Free up space before running.",
        "it": "Solo {mb:.0f} MB liberi in `data/`. Libera spazio prima di elaborare.",
    },
    "process.prisma_needs_pair": {
        "en": "**{product}**: PRISMA needs *both* files — the L1 you selected **and** "
              "its L2C companion `{companion}` in the same folder. Add "
              "`{companion}` to `data/input/` and reload.",
        "it": "**{product}**: PRISMA richiede *entrambi* i file — l'L1 selezionato "
              "**e** il suo file L2C `{companion}` nella stessa cartella. Aggiungi "
              "`{companion}` in `data/input/` e ricarica.",
    },
    "process.prisma_needs_creds": {
        "en": "PRISMA also needs meteorological data (ozone / wind / pressure) that "
              "Polymer downloads from NASA Earthdata. Add a **NASA Earthdata** "
              "account (or a **Copernicus CDS** key) in the **Setup** tab first.",
        "it": "PRISMA richiede anche dati meteo (ozono / vento / pressione) che "
              "Polymer scarica da NASA Earthdata. Inserisci prima un account "
              "**NASA Earthdata** (o una chiave **Copernicus CDS**) nella scheda "
              "**Configurazione**.",
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
    "process.run": {"en": "Run Polymer", "it": "Avvia Polymer"},
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
    "history.col.output": {"en": "output", "it": "output"},
    "history.col.version": {"en": "version", "it": "versione"},
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
