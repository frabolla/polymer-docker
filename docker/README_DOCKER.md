# Polymer in Docker, with a graphical interface

> 🇮🇹 Versione italiana: [README_DOCKER.it.md](README_DOCKER.it.md)
>
> 🐣 Never used Docker? Follow the fully step-by-step, click-by-click guide:
> **[HOWTO.md](HOWTO.md)** (🇮🇹 [HOWTO.it.md](HOWTO.it.md)).

This folder contains everything needed to use **Polymer** without installing
Python, without compiling anything and without the command line. Parameters are
set from a web page that opens in your browser. The interface is in English by
default; Italian can be selected from the sidebar.

> **Licence.** Polymer belongs to HYGEOS and **may not be redistributed** (see
> `LICENCE.TXT`, Section 2). That is why only the *build recipe* is provided here:
> the Docker image is built on your own computer, locally. On first run you must
> accept Polymer's Terms of use.

---

## 1. Install Docker Desktop (once)

| System | Link |
|---|---|
| Windows 10/11 | <https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe> |
| macOS (Apple Silicon: M1/M2/M3/M4) | <https://desktop.docker.com/mac/main/arm64/Docker.dmg> |
| macOS (Intel) | <https://desktop.docker.com/mac/main/amd64/Docker.dmg> |
| Linux | <https://docs.docker.com/desktop/install/linux/> |

Install it, start **Docker Desktop** and wait until the whale icon is steady
("running").

## 2. Download this repository

- Green **Code → Download ZIP** button on GitHub, then extract the folder;
- or, if you have git: `git clone <repository-url>`.

## 3. Start Polymer

Open the `docker/launchers/` folder and **double-click**:

- **Windows** → `Start-Polymer-Windows.bat`
  (first time: on the *"Windows protected your PC"* box, **More info → Run anyway**)
- **macOS / Linux** → `Start-Polymer-macOS-Linux.command`

**macOS, one-time unlock.** A launcher from a downloaded ZIP is quarantined by
Gatekeeper and loses its runnable flag. In **Terminal**, run once (drag the files
in so you don't type paths):

```bash
xattr -dr com.apple.quarantine  <the unzipped project folder>
chmod +x  <the unzipped project folder>/docker/launchers/Start-Polymer-macOS-Linux.command
```

Then double-click it. If macOS still blocks it, right-click → **Open** → **Open**,
or **System Settings → Privacy & Security → Open Anyway**. (With `git clone`
instead of a ZIP this is not needed.)

The **first run** takes **10–20 minutes** (it downloads ~4 GB of scientific
libraries and compiles the compute modules). Later starts are almost instant.

When it is ready, the browser opens by itself at **<http://localhost:8501>**.

> Alternatively, from a terminal in the repository folder:
> ```bash
> docker compose -f docker/docker-compose.yml up --build
> ```

## 4. First-time setup (in the interface)

1. **Accept Polymer's Terms of use.**
2. **Setup → Download auxiliary data** (about 1 GB, once).
3. *(Optional)* **Setup → Meteorological data credentials**: enter your
   [NASA Earthdata](https://urs.earthdata.nasa.gov/users/new) username/password
   or your [CDS API key](https://cds.climate.copernicus.eu/user/register).
   Without credentials, Polymer still works for most sensors using built-in
   climatologies — **except PRISMA**, which requires this download and will not
   run without a NASA Earthdata (or Copernicus CDS) account.

## 5. Process a product

1. Get your **Level-1** products into `data/input/`, either by copying them into
   the folder that appeared next to the repository (`.SEN3` folders for
   Sentinel-3 OLCI, `.SAFE` for Sentinel-2 MSI, `.he5` for PRISMA, `.N1` for
   MERIS, `.L1C` for MODIS/VIIRS/SeaWiFS…) **or** with the **Upload a product**
   panel on the Processing tab (drop a `.zip` for folder products, or a
   single-file product).
2. On the **Processing** tab: pick the product; with sensor `auto` the
   interface shows the detected sensor (for **PRISMA** and **HICO** choose it
   manually); set the output format and the parameters.
3. Press **Run Polymer**. A progress bar and the log update while it runs; you
   can **Cancel** at any time. It keeps running if you switch tabs.
4. Select **several products at once** for batch processing — a summary table
   shows which succeeded, and a button re-runs just the failed ones.
5. Browse outputs on the **Results** tab: pick a file, choose a variable (or the
   automatic RGB / chlorophyll view), see a histogram, and download the file.

## 6. Stop / update

- Stop: `docker compose -f docker/docker-compose.yml down`
- Update after a `git pull`: restart with the launcher (it rebuilds if needed) or
  `docker compose -f docker/docker-compose.yml up --build`.

## Where the data goes

A `data/` folder is created next to the repository:

| Folder | Content |
|---|---|
| `data/input` | Level-1 products to process (you put them here) |
| `data/output` | Level-2 results + `_jobs.log` (history) |
| `data/auxdata` | Polymer static tables (downloaded once) |
| `data/ancillary` | meteorological data downloaded automatically |
| `data/config` | credentials (`.netrc`, `.cdsapirc`), language and licence consent |

None of this data lives inside the image: you can delete and rebuild the image
without losing your setup and downloads.

## Troubleshooting

| Problem | Fix |
|---|---|
| "port 8501 already in use" | change `127.0.0.1:8501:8501` to `127.0.0.1:8502:8501` in `docker/docker-compose.yml` and open `http://localhost:8502` |
| Build failed halfway | `docker compose -f docker/docker-compose.yml build --no-cache` |
| Processing slower than expected on Apple Silicon | a native `arm64` image is built automatically. If your Docker is set to force `linux/amd64`, disable that so it builds native. |
| "out of memory" during processing | in Docker Desktop → *Settings → Resources* raise the RAM (≥ 8 GB recommended) |
| Need more disk space | the image + auxiliary data take ~6–7 GB |

## Known limits

- The image builds natively for `linux/amd64` and `linux/arm64` (Apple Silicon
  uses a version-pinned `docker/environment.arm64.yml` instead of the amd64 lock).
- **PRISMA needs two files** (`PRS_L1_STD_OFFL_*.he5` **and** `PRS_L2C_STD_*.he5`,
  same name, both in `data/input/`) **and** a NASA Earthdata / Copernicus CDS
  account for the meteo data. The interface checks both and refuses to start
  otherwise, with a message telling you what is missing.
- MODIS/VIIRS/SeaWiFS need **Level-1C** files prepared beforehand with `l2gen`
  (NASA OBPG), which is not included here.
- The interface uses Polymer's v4 API (`run_atm_corr`), which covers every sensor
  listed above.
