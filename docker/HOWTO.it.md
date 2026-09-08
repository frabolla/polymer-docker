# GUIDA — Usare Polymer per la prima volta (tutto grafico, con Docker Desktop)

> 🇬🇧 English version: [HOWTO.md](HOWTO.md)

Questa guida è per chi **non ha mai usato Docker** e vuole fare **tutto con il
mouse** — nessun comando, niente da digitare.

Userai solo tre cose:

1. **Docker Desktop** — un'applicazione con una normale finestra, pulsanti e menu.
2. **Un avviatore (launcher)** — un file su cui fai doppio clic.
3. **L'interfaccia di Polymer** — una normale pagina web nel browser.

Le Parti 1–3 si fanno una volta sola. Dopo, usare Polymer è un doppio clic.

---

## Parte 1 — Installare Docker Desktop

### Windows 10 / 11

1. Scarica il programma di installazione:
   <https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe>
2. Fai doppio clic su **`Docker Desktop Installer.exe`**.
3. Lascia tutte le opzioni come proposte (mantieni spuntato **"Use WSL 2"**) e
   clicca **OK**. Se l'installazione propone di aggiungere componenti di Windows,
   **accetta**.
4. Al termine clicca **"Close and restart"**. Il PC si riavvia.
5. Dopo il riavvio apri **Docker Desktop** dal menu Start.
6. Nella finestra clicca **Accept** sul *Docker Subscription Service Agreement*
   (gratuito per uso personale).
7. Nella schermata di accesso clicca **"Continue without signing in"**, poi salta
   il sondaggio.
8. Guarda vicino all'orologio (in basso a destra; clicca la piccola **^** per
   mostrare le icone nascoste): compare l'icona di una balena 🐳. Aspetta che
   smetta di muoversi.

> Se Windows segnala che manca "WSL 2" anche dopo il riavvio, apri il messaggio
> di Docker Desktop stesso — ha un **pulsante** che lo installa per te — oppure
> segui <https://docs.docker.com/desktop/setup/install/windows-install/>.

### macOS

1. Scopri che Mac hai: menu **Apple ** (in alto a sinistra) → **Informazioni
   su questo Mac**.
   - Dice **"Chip: Apple M1 / M2 / M3 / M4"** → hai un **Apple Silicon**.
   - Dice **"Processore: Intel"** → hai un **Intel**.
2. Scarica il programma di installazione giusto:
   - Apple Silicon: <https://desktop.docker.com/mac/main/arm64/Docker.dmg>
   - Intel: <https://desktop.docker.com/mac/main/amd64/Docker.dmg>
3. Fai doppio clic sul file **`Docker.dmg`** scaricato. Si apre una finestra con
   l'icona **Docker** e la cartella **Applicazioni** — trascina l'icona Docker
   sulla cartella Applicazioni.
4. Apri il **Launchpad** o la cartella **Applicazioni** e clicca **Docker**.
5. Un avviso dice che l'app è stata scaricata da Internet → clicca **Apri**.
6. Un avviso chiede l'**accesso privilegiato** → digita la password del tuo Mac e
   conferma (succede solo la prima volta).
7. Clicca **Accept** sull'accordo, poi **"Continue without signing in"**.
8. Compare l'icona di una balena 🐳 nella barra dei menu in alto. Aspetta che
   smetta di muoversi.

### Linux

Installa **Docker Desktop per Linux** scaricando il pacchetto per la tua
distribuzione da <https://docs.docker.com/desktop/setup/install/linux/> e
aprendolo con il tuo gestore di applicazioni, poi avvia **Docker Desktop** dal
menu delle applicazioni.

---

## Parte 2 — Verificare che Docker Desktop sia pronto

1. Apri la finestra di **Docker Desktop** (clicca l'icona della balena 🐳, poi
   **"Dashboard"** / **"Open Docker Desktop"** se serve).
2. Guarda l'**angolo in basso a sinistra** della finestra: devi vedere un
   **pallino verde** e la scritta **"Engine running"**.

✅ Se c'è scritto **"Engine running"**, sei pronto. Puoi ridurre a icona la
finestra; lascia l'app aperta.

---

## Parte 3 — Scaricare Polymer

1. Apri la pagina del progetto su GitHub nel browser.
2. Clicca il pulsante verde **`Code`**, poi **Download ZIP**.
3. Apri la cartella **Download** ed **estrai** (decomprimi) il file:
   - Windows: tasto destro sullo ZIP → **Estrai tutto… → Estrai**.
   - macOS: doppio clic sullo ZIP.
4. Ora hai una cartella, ad es. **`polymer-docker-main`**. Trascinala nella tua
   cartella **Documenti** così la ritrovi facilmente.

---

## Parte 4 — Primo avvio

1. Apri la cartella della Parte 3, poi **`docker`**, poi **`launchers`**.

2. **Solo macOS — sblocco una tantum.** Un launcher preso da uno ZIP scaricato
   viene bloccato da macOS (Gatekeeper) e non è marcato come eseguibile. Fai
   questo una volta sola:
   1. Apri il **Terminale** (premi ⌘ + Spazio, scrivi `Terminale`, premi Invio).
   2. Nella finestra del Terminale scrivi `xattr -dr com.apple.quarantine `
      (lascia lo spazio finale), poi **trascina la cartella del progetto** dal
      Finder sulla finestra del Terminale e premi **Invio**.
   3. Scrivi `chmod +x ` (di nuovo, lascia lo spazio finale), **trascina**
      `docker/launchers/Start-Polymer-macOS-Linux.command` dal Finder sulla
      finestra del Terminale e premi **Invio**.

   (Se hai ottenuto il progetto con `git clone` invece che da ZIP, puoi saltare
   questo passo — git mantiene il file eseguibile.)

3. Fai doppio clic sul file per il tuo sistema:
   - **Windows** → **`Start-Polymer-Windows.bat`**
   - **macOS / Linux** → **`Start-Polymer-macOS-Linux.command`**

   **macOS — solo la prima volta:** se compare ancora *"impossibile aprire perché
   proviene da uno sviluppatore non identificato"* (o *"Apple non può
   verificare…"*): tasto destro sul file → **Apri** → **Apri**. Se non c'è il
   pulsante **Apri**, vai in **Impostazioni di Sistema → Privacy e sicurezza**,
   scorri in fondo, clicca **Apri comunque** accanto al messaggio su
   `Start-Polymer-macOS-Linux.command`, poi conferma con **Apri**. Dopo, il
   doppio clic normale funziona.
   **Windows — solo la prima volta:** se compare il riquadro blu *"Windows ha
   protetto il PC"*, clicca **Ulteriori informazioni → Esegui comunque**.

4. Compare una piccola finestra con del testo che scorre — sono solo informazioni
   di avanzamento. **Non devi digitare nulla.** Puoi spostarla di lato.
   **Il primo avvio richiede 10–20 minuti**: sta scaricando e preparando il
   programma. Succede **solo una volta**.

5. Quando è pronto, il browser si apre da solo su
   **<http://localhost:8501>**.
   Se non si apre, scrivi tu quell'indirizzo nel browser, oppure usa il metodo
   con Docker Desktop della Parte 7.

✅ Devi vedere una pagina intitolata **"Polymer — Termini d'uso"**.

---

## Parte 5 — Configurare Polymer (nella pagina web)

### 5.1 Lingua

In **alto a sinistra** nella pagina c'è un menu **Lingua**. L'inglese è
predefinito; scegli **Italiano** se preferisci. La scelta viene ricordata.

### 5.2 Accettare i termini

Leggi il testo, spunta la casella **"Ho letto e accetto i Termini d'uso di
Polymer"**, poi clicca **Continua**.

### 5.3 Scaricare i dati ausiliari

1. Clicca la scheda **Configurazione**.
2. Clicca il pulsante **"Scarica / aggiorna dati ausiliari"**.
3. Aspetta il download di circa **1 GB** di tabelle di riferimento. Il testo
   scorre nella pagina per mostrare l'avanzamento. Si fa **solo una volta**.

✅ Nella barra laterale a sinistra, la riga **"Dati ausiliari statici"** diventa
una spunta verde ✅.

### 5.4 (Facoltativo) Account per i dati meteo

Polymer può scaricare da solo ozono / vento / pressione se hai un account
gratuito. Senza, funziona comunque per la maggior parte dei sensori usando dati
interni — ma **PRISMA non parte** senza un account NASA Earthdata o Copernicus CDS.

- Scheda **Configurazione** → **"Fonte dei dati meteo"** → scegli **NASA
  Earthdata** oppure **Copernicus ERA5 / CDS**.
- Scrivi nome utente e password (NASA) o la API key (CDS), poi clicca **Salva**.
  I link per registrarsi sono mostrati subito sotto i campi.

---

## Parte 6 — Elaborare un prodotto satellitare

1. Metti i tuoi prodotti **Level-1** nella cartella **`data/input`**. Questa
   cartella è **dentro la cartella che hai decompresso nella Parte 3**
   (`…/polymer-docker-main/data/input`). È comparsa da sola al primo avvio.
   Trascina dentro le cartelle/file dei prodotti con il mouse.

   Accettati: cartelle `.SEN3` (Sentinel-3 OLCI), cartelle `.SAFE`
   (Sentinel-2 MSI), file `.he5` (PRISMA), file `.N1` (MERIS), file `.L1C`
   (MODIS / VIIRS / SeaWiFS).

   **PRISMA richiede due file:** il Level-1 (`PRS_L1_STD_OFFL_….he5`) **e** il
   suo file Level-2C (`PRS_L2C_STD_….he5`, stesso nome). Metti **entrambi** in
   `data/input`; nell'interfaccia seleziona solo l'L1. PRISMA richiede **anche un
   account NASA Earthdata (o Copernicus CDS)** per i dati meteo — inseriscilo
   prima nella scheda Configurazione. Se manca qualcosa l'interfaccia te lo
   segnala e non parte.

   In alternativa usa il pannello **Carica un prodotto** nella scheda
   Elaborazione: trascina uno `.zip` per i prodotti a cartella, o un prodotto a
   file singolo.

2. Torna al browser e **ricarica la pagina** (premi **F5**, o ⌘R su Mac).
3. Clicca la scheda **Elaborazione**:
   - **Prodotti Level-1 da elaborare** — clicca per sceglierne uno (o più, per
     l'elaborazione in lotto).
   - **Sensore** — lascia **auto**; la pagina mostra il sensore rilevato. Per
     **PRISMA** e **HICO** scegli tu dall'elenco.
   - **Formato di output** — `hdf4` (predefinito, formato nativo di Polymer) o
     `netcdf4` (più portabile). I valori dei pixel sono identici.
   - **Parametri comuni** — cambiali solo se serve (numero di core CPU, un
     eventuale ritaglio della scena).
4. Clicca **Avvia Polymer**. Durante l'elaborazione si aggiornano una barra di
   avanzamento e il log; un pulsante **Annulla** la interrompe. Continua anche
   se cambi scheda.
5. Al termine il file risultato è nella cartella **`data/output`**. Se hai
   elaborato più prodotti, una tabella riepilogo mostra quali sono riuscite e un
   pulsante ripete solo i falliti.
6. Apri la scheda **Risultati**: scegli il file di output e clicca **Scarica
   questo file**, oppure usa il pannello *Cartelle di lavoro* per aprire la
   cartella `data/output` sul tuo computer. C'è un "controllo visivo rapido"
   facoltativo che mostra una piccola anteprima RGB — solo per confermare che la
   correzione è stata eseguita; ciò che conta è il file. A fine elaborazione
   senti anche un breve suono e vedi una conferma verde.

La scheda **Cronologia** mostra una tabella delle elaborazioni precedenti.

---

## Parte 7 — Gestire Polymer dalla finestra di Docker Desktop

Tutto qui sotto si fa con i pulsanti della finestra di Docker Desktop — senza
digitare nulla.

1. Apri **Docker Desktop** e clicca **Containers** nel menu a sinistra.
2. Vedi una riga chiamata **`polymer-gui`**.

| Vuoi… | Clicca… |
|---|---|
| **Aprire l'interfaccia** | il link blu **`8501:8501`** su quella riga — apre il browser sulla pagina di Polymer |
| **Fermare Polymer** | il pulsante **■ (Stop)** su quella riga |
| **Riavviarlo** | il pulsante **▶ (Start)** su quella riga |
| **Vedere cosa sta facendo** | il **nome** del container → la scheda **Logs** |
| **Eliminarlo** (per ricostruirlo da capo) | il pulsante **🗑 (Delete)** — la cartella `data/` viene conservata |

Per avviare Polymer dopo aver spento il computer: assicurati che Docker Desktop
mostri **"Engine running"**, poi fai doppio clic sul launcher (Parte 4) oppure
premi **▶** sulla riga `polymer-gui`.

---

## Parte 8 — Impostazioni e riparazione (tutto nella finestra di Docker Desktop)

Apri **Docker Desktop**, poi clicca l'**icona a ingranaggio ⚙ (Settings)** in
alto.

- **Dare più memoria a Polymer:** **Resources** → trascina il cursore **Memory**
  ad almeno **8 GB** → **Apply & restart**. Fallo se l'elaborazione si ferma con
  un messaggio "out of memory".
- **Ripartire da zero se qualcosa è rotto:** clicca l'**icona a coleottero 🐞
  (Troubleshoot)** in alto → **"Clean / Purge data"** (oppure **"Reset to
  factory defaults"**). Poi rifai la Parte 4 (ricostruirà).
- **Liberare spazio su disco:** **Images** nel menu a sinistra → seleziona
  **`polymer-gui`** → **Delete**. I tuoi prodotti e risultati in `data/` non
  vengono toccati.

---

## Parte 9 — Aggiornare a una nuova versione

1. In Docker Desktop → **Containers** → premi **■ (Stop)** su `polymer-gui`.
2. Scarica il nuovo **ZIP** da GitHub e decomprimilo sopra la vecchia cartella
   (sostituisci quando richiesto), tenendo la tua cartella `data/`.
3. Fai di nuovo doppio clic sul launcher. Ricostruisce solo ciò che è cambiato,
   quindi è veloce.

---

## Problemi comuni

| Cosa vedi | Cosa fare |
|---|---|
| La finestra del launcher dice **"Docker is not running"** | Apri Docker Desktop, aspetta **"Engine running"** (in basso a sinistra), poi rifai doppio clic sul launcher. |
| L'icona della balena 🐳 continua a muoversi / **"Docker Desktop starting…"** non finisce mai | Tasto destro sulla balena → **Restart**. Se resta bloccato → riavvia il computer. |
| Il browser dice che **non riesce a connettersi** a `localhost:8501` | Al primo avvio aspetta qualche minuto in più. Poi controlla Docker Desktop → **Containers**: la riga `polymer-gui` deve dire **Running**. Clicca il suo link **`8501:8501`**. |
| Messaggio **"port 8501 already in use"** | Un altro programma sta usando quel numero. Chiudilo, oppure apri `docker/docker-compose.yml` con un editor di testo (Blocco note / TextEdit), cambia `127.0.0.1:8501:8501` in `127.0.0.1:8502:8501`, salva, riavvia Polymer e usa <http://localhost:8502>. |
| L'elaborazione si ferma con **"out of memory"** | Docker Desktop → ⚙ **Settings → Resources** → alza **Memory** a 8 GB+ → **Apply & restart**. |
| L'elaborazione è **più lenta del previsto su un Mac Apple Silicon** | Viene costruita in automatico una versione nativa Apple Silicon. Se sembra ancora emulata, controlla che Docker Desktop non stia forzando "Rosetta" / `linux/amd64` per questa immagine. |
| Non funziona niente, vuoi ripartire pulito | Docker Desktop → 🐞 **Troubleshoot → Clean / Purge data**, poi rifai la Parte 4. |

---

## Buono a sapersi

- Polymer è di HYGEOS e **non può essere condiviso o ridistribuito** (vedi
  `LICENCE.TXT`). Lo costruisci sul tuo computer e accetti i termini nella prima
  pagina.
- I tuoi prodotti, risultati, download, lingua e impostazioni stanno tutti nella
  cartella **`data/`** accanto al progetto decompresso — mai dentro Docker. Puoi
  cancellare e ricostruire il container senza perderli.
- MODIS / VIIRS / SeaWiFS richiedono file **Level-1C** preparati prima con
  `l2gen` (NASA OBPG); quel passaggio non fa parte di questo strumento.
