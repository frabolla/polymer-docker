# Polymer in Docker, con interfaccia grafica

> 🇬🇧 English version: [README_DOCKER.md](README_DOCKER.md)
>
> 🐣 Non hai mai usato Docker? Segui la guida passo-passo, clic per clic:
> **[HOWTO.it.md](HOWTO.it.md)** (🇬🇧 [HOWTO.md](HOWTO.md)).

Questa cartella contiene tutto il necessario per usare **Polymer** senza installare
Python, senza compilare nulla e senza usare la riga di comando. I parametri si
impostano da una pagina web che si apre nel browser. L'interfaccia è in inglese di
default; l'italiano si seleziona dalla barra laterale.

> **Licenza.** Polymer è di HYGEOS e **non può essere ridistribuito** (vedi
> `LICENCE.TXT`, Sezione 2). Per questo qui trovi solo le *istruzioni di
> costruzione*: l'immagine Docker viene creata sul tuo computer, in locale.
> Al primo avvio dovrai accettare i Termini d'uso di Polymer.

---

## 1. Installa Docker Desktop (una volta sola)

| Sistema | Link |
|---|---|
| Windows 10/11 | <https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe> |
| macOS (Apple Silicon: M1/M2/M3/M4) | <https://desktop.docker.com/mac/main/arm64/Docker.dmg> |
| macOS (Intel) | <https://desktop.docker.com/mac/main/amd64/Docker.dmg> |
| Linux | <https://docs.docker.com/desktop/install/linux/> |

Installa, avvia **Docker Desktop** e aspetta che l'icona della balena sia stabile
(stato "running").

## 2. Scarica questo repository

- Pulsante verde **Code → Download ZIP** su GitHub, poi estrai la cartella;
- oppure, se hai git: `git clone <url-del-repository>`.

## 3. Avvia Polymer

Apri la cartella `docker/launchers/` e fai **doppio clic** su:

- **Windows** → `Start-Polymer-Windows.bat`
  (la prima volta: sul riquadro *"Windows ha protetto il PC"*, **Ulteriori
  informazioni → Esegui comunque**)
- **macOS / Linux** → `Start-Polymer-macOS-Linux.command`

**macOS, sblocco una tantum.** Un launcher preso da uno ZIP scaricato viene messo
in quarantena da Gatekeeper e perde il flag di eseguibile. Nel **Terminale**
esegui una volta (trascina i file per non digitare i percorsi):

```bash
xattr -dr com.apple.quarantine  <la cartella del progetto decompressa>
chmod +x  <la cartella del progetto decompressa>/docker/launchers/Start-Polymer-macOS-Linux.command
```

Poi fai doppio clic. Se macOS lo blocca ancora, tasto destro → **Apri** →
**Apri**, oppure **Impostazioni di Sistema → Privacy e sicurezza → Apri
comunque**. (Con `git clone` invece dello ZIP non serve.)

La **prima volta** la costruzione richiede **10–20 minuti** (scarica ~4 GB di
librerie scientifiche e compila i moduli di calcolo). Le volte successive l'avvio è
quasi immediato.

Quando è pronto, il browser si apre da solo su **<http://localhost:8501>**.

> In alternativa, da un terminale nella cartella del repository:
> ```bash
> docker compose -f docker/docker-compose.yml up --build
> ```

## 4. Prima configurazione (nell'interfaccia)

Al primo avvio si apre una pagina dedicata **"Configura Polymer — una volta
sola"**. Completati i tre passaggi qui sotto, lascia il posto all'interfaccia di
lavoro, dove **Elaborazione** è la scheda principale. Tutto ciò che inserisci
viene salvato in `data/config/` e riutilizzato a ogni avvio successivo.

1. **Accetta i Termini d'uso** di Polymer.
2. **Scarica dati ausiliari** (circa 1 GB, una volta sola).
3. **Credenziali dati meteo**: inserisci
   l'utente/password di [NASA Earthdata](https://urs.earthdata.nasa.gov/users/new)
   oppure la [CDS API key](https://cds.climate.copernicus.eu/user/register).
   Senza credenziali, Polymer funziona per la maggior parte dei sensori usando
   climatologie interne — **tranne PRISMA**, che richiede questo download e non
   parte senza un account NASA Earthdata (o Copernicus CDS).

## 5. Elabora un prodotto

1. Porta i tuoi prodotti **Level-1** in `data/input/`, copiandoli nella cartella
   comparsa accanto al repository (cartelle `.SEN3` per Sentinel-3 OLCI, `.SAFE`
   per Sentinel-2 MSI, `.he5` per PRISMA, `.N1` per MERIS, `.L1C` per
   MODIS/VIIRS/SeaWiFS…) **oppure** con il pannello **Carica un prodotto** nella
   scheda Elaborazione (trascina uno `.zip` per i prodotti a cartella, o un
   prodotto a file singolo).
   *Per tenere i dati altrove (es. un disco esterno) usa **Cartelle di lavoro →
   Cambia le cartelle input / output** e riavvia dal launcher.*
2. Nella scheda **Elaborazione**: seleziona il prodotto; con sensore `auto`
   l'interfaccia mostra il sensore rilevato (per **PRISMA** e **HICO** sceglilo a
   mano); imposta formato di output e parametri.
3. Premi **Avvia Polymer**. Durante l'elaborazione si aggiornano una barra di
   avanzamento e il log; puoi **Annullare** in qualsiasi momento. Continua anche
   se cambi scheda.
4. Seleziona **più prodotti insieme** per l'elaborazione in lotto — una tabella
   riepilogo mostra quali sono riuscite e un pulsante ripete solo i falliti.
5. Nella scheda **Risultati**: scegli un file di output e **Scaricalo**, oppure
   copia il percorso di `data/output` dal pannello *Cartelle di lavoro* per
   aprirlo sul tuo computer. Un "controllo visivo rapido" facoltativo mostra una
   piccola anteprima RGB solo per confermare che la correzione è stata eseguita —
   l'output vero è il file stesso (HDF per impostazione predefinita).

## 6. Fermare / aggiornare

- Fermare: `docker compose -f docker/docker-compose.yml down`
- Aggiornare dopo un `git pull`: riavvia con il launcher (ricostruisce se serve) o
  `docker compose -f docker/docker-compose.yml up --build`.

## Dove finiscono i dati

Accanto al repository viene creata la cartella `data/`:

| Cartella | Contenuto |
|---|---|
| `data/input` | prodotti Level-1 da elaborare (li metti tu) |
| `data/output` | risultati Level-2 + `_jobs.log` (cronologia) |
| `data/auxdata` | tabelle statiche di Polymer (scaricate una volta) |
| `data/ancillary` | dati meteo scaricati automaticamente |
| `data/config` | credenziali (`.netrc`, `.cdsapirc`), lingua e consenso alla licenza |

Nessuno di questi dati è dentro l'immagine: puoi cancellare e ricostruire
l'immagine senza perdere configurazione e download.

## Risoluzione problemi

| Problema | Soluzione |
|---|---|
| «porta 8501 già in uso» | cambia `127.0.0.1:8501:8501` in `127.0.0.1:8502:8501` in `docker/docker-compose.yml` e vai su `http://localhost:8502` |
| Build fallita a metà | `docker compose -f docker/docker-compose.yml build --no-cache` |
| Elaborazione più lenta del previsto su Apple Silicon | viene costruita automaticamente un'immagine `arm64` nativa. Se il tuo Docker è impostato per forzare `linux/amd64`, disattivalo così costruisce nativa. |
| «out of memory» durante l'elaborazione | in Docker Desktop → *Settings → Resources* aumenta la RAM (consigliati ≥ 8 GB) |
| Serve più spazio disco | l'immagine + dati ausiliari occupano ~6–7 GB |

## Limiti noti

- L'immagine si costruisce nativa per `linux/amd64` e `linux/arm64` (su Apple
  Silicon usa `docker/environment.arm64.yml` con versioni fissate, non il lock amd64).
- **PRISMA richiede due file** (`PRS_L1_STD_OFFL_*.he5` **e** `PRS_L2C_STD_*.he5`,
  stesso nome, entrambi in `data/input/`) **e** un account NASA Earthdata /
  Copernicus CDS per i dati meteo. L'interfaccia controlla entrambi e non parte
  altrimenti, indicando cosa manca.
- MODIS/VIIRS/SeaWiFS richiedono file **Level-1C** già preparati con `l2gen` (NASA
  OBPG), non incluso qui.
- L'interfaccia usa l'API v4 di Polymer (`run_atm_corr`), che copre tutti i sensori
  elencati sopra.
