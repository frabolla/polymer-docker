# Polymer in Docker, con interfaccia grafica

Questa cartella contiene tutto il necessario per usare **Polymer** senza installare
Python, senza compilare nulla e senza usare la riga di comando. I parametri si
impostano da una pagina web che si apre nel browser.

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

- **Windows** → `Avvia-Polymer-Windows.bat`
- **macOS / Linux** → `Avvia-Polymer-macOS-Linux.command`
  (su macOS la prima volta: tasto destro → **Apri** per superare il blocco Gatekeeper)

La **prima volta** la costruzione richiede **10–20 minuti** (scarica ~4 GB di
librerie scientifiche e compila i moduli di calcolo). Le volte successive l'avvio è
quasi immediato.

Quando è pronto, il browser si apre da solo su **<http://localhost:8501>**.

> In alternativa, da un terminale nella cartella del repository:
> ```bash
> docker compose -f docker/docker-compose.yml up --build
> ```

## 4. Prima configurazione (nell'interfaccia)

1. **Accetta i Termini d'uso** di Polymer.
2. Scheda **Configurazione → Scarica dati ausiliari** (circa 1 GB, una volta sola).
3. *(Facoltativo)* Scheda **Configurazione → Credenziali dati meteo**: inserisci
   l'utente/password di [NASA Earthdata](https://urs.earthdata.nasa.gov/users/new)
   oppure la [CDS API key](https://cds.climate.copernicus.eu/user/register).
   Senza credenziali, Polymer usa comunque delle climatologie interne.

## 5. Elabora un prodotto

1. Copia i tuoi prodotti **Level-1** nella cartella `data/input/` che è comparsa
   accanto al repository (cartelle `.SEN3` per Sentinel-3 OLCI, `.SAFE` per
   Sentinel-2 MSI, file `.he5` per PRISMA, `.N1` per MERIS, `.L1C` per MODIS/VIIRS/SeaWiFS…).
2. Nella scheda **Elaborazione**: seleziona il prodotto, il sensore (`auto` va bene
   nella maggior parte dei casi; per **PRISMA** e **HICO** scegli il sensore a mano),
   il formato di output e i parametri.
3. Premi **▶ Avvia Polymer**. Il registro di elaborazione scorre a schermo.
4. Al termine trovi il risultato in `data/output/` e un'anteprima nell'interfaccia.

Puoi selezionare **più prodotti insieme** per l'elaborazione in lotto.

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
| `data/config` | credenziali (`.netrc`, `.cdsapirc`) e consenso alla licenza |

Nessuno di questi dati è dentro l'immagine: puoi cancellare e ricostruire
l'immagine senza perdere configurazione e download.

## Risoluzione problemi

| Problema | Soluzione |
|---|---|
| «porta 8501 già in uso» | cambia `8501:8501` in `8502:8501` in `docker/docker-compose.yml` e vai su `http://localhost:8502` |
| Build fallita a metà | `docker compose -f docker/docker-compose.yml build --no-cache` |
| Elaborazione lenta su Mac Apple Silicon | normale: l'immagine è `linux/amd64` ed è emulata. Funziona, ma è più lenta. |
| «out of memory» durante l'elaborazione | in Docker Desktop → *Settings → Resources* aumenta la RAM (consigliati ≥ 8 GB) |
| Serve più spazio disco | l'immagine + dati ausiliari occupano ~6–7 GB |

## Limiti noti

- L'immagine è solo `linux/amd64` (il lock `environment.yml` è per quella piattaforma).
- MODIS/VIIRS/SeaWiFS richiedono file **Level-1C** già preparati con `l2gen` (NASA
  OBPG), non incluso qui.
- L'interfaccia usa l'API v4 di Polymer (`run_atm_corr`), che copre tutti i sensori
  elencati sopra.
