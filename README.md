# Polymer — Docker container with a graphical interface

Run **Polymer** (atmospheric correction of sun-glint contaminated ocean colour
observations) from a web page in your browser, with no Python environment and no
command line.

> ### This repository is a fork
>
> This is a **fork** of the open-source Polymer algorithm by HYGEOS.
> Original software and full scientific/algorithm documentation:
> **<https://github.com/hygeos/polymer>**.
>
> This fork adds only the packaging in [`docker/`](docker/) — a Docker image plus
> a graphical interface, by **Francesco Tarini**
> ([@frabolla](https://github.com/frabolla)). The Polymer algorithm itself is
> unchanged.
>
> Polymer is **free for non-commercial use** and **must not be redistributed**
> (see [`LICENCE.TXT`](LICENCE.TXT)). For that reason no ready-made image is
> published: you build it locally from this repository, and accept the terms on
> first run.

---

## First run (once)

1. Install **Docker Desktop** and wait until it shows *Engine running*.
   - Windows: <https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe>
   - macOS (Apple Silicon): <https://desktop.docker.com/mac/main/arm64/Docker.dmg>
   - macOS (Intel): <https://desktop.docker.com/mac/main/amd64/Docker.dmg>
   - Linux: <https://docs.docker.com/desktop/setup/install/linux/>
2. Download this repository: green **Code → Download ZIP**, then unzip it.
3. Open `docker/launchers/` and double-click the launcher for your system:
   - **Windows** → `Start-Polymer-Windows.bat`
   - **macOS / Linux** → `Start-Polymer-macOS-Linux.command`
     (macOS first time: right-click → **Open**)

   The first build takes **10–20 minutes** (it downloads ~4 GB of scientific
   libraries and compiles the modules). This happens only once.
4. The browser opens at **<http://localhost:8501>**. In the page:
   - accept the **Terms of use**;
   - **Setup** tab → **Download auxiliary data** (~1 GB, once);
   - *(optional)* enter a **NASA Earthdata** or **Copernicus CDS** account so
     Polymer can fetch weather data automatically (otherwise built-in
     climatologies are used).
5. Put your **Level-1** products in the `data/input/` folder next to the project
   (`.SEN3` folders for Sentinel-3 OLCI, `.SAFE` for Sentinel-2 MSI, `.he5` for
   PRISMA, `.N1` for MERIS, `.L1C` for MODIS/VIIRS/SeaWiFS) — or use the in-app
   **Upload a product** panel. Reload the page.
6. **Processing** tab → pick one or more products and a sensor (`auto` shows the
   detected one) → **Run Polymer**. A progress bar and a Cancel button track the
   run; batches get a summary with a "re-run failed" button.
7. **Results** tab → browse the output files, preview any variable with a
   histogram, and download.

## After an update (no full rebuild)

When a new version of this project is released you do **not** rebuild from
scratch:

1. Stop the container: Docker Desktop → **Containers** → **Stop** on `polymer-gui`.
2. Overwrite the project folder with the new version (new ZIP, or `git pull`),
   **keeping the `data/` folder**.
3. Run the launcher again. Docker reuses the cached layers and rebuilds only what
   changed — usually under a minute.

Your auxiliary data, credentials, language and history all live in `data/` and
are kept across updates. Re-download the auxiliary data only if the app says it
is missing.

## Where your files are

A `data/` folder is created next to the project:

| Folder | Content |
|---|---|
| `data/input` | Level-1 products to process (you put them here) |
| `data/output` | Level-2 results + `_jobs.log` (history) |
| `data/auxdata` | Polymer static tables (downloaded once) |
| `data/ancillary` | weather data downloaded automatically |
| `data/config` | credentials, language, licence acceptance |

Nothing is stored inside the container — you can delete and rebuild it without
losing your setup.

## Documentation

- **Never used Docker?** Click-by-click guide: [`docker/HOWTO.md`](docker/HOWTO.md)
  · 🇮🇹 [`docker/HOWTO.it.md`](docker/HOWTO.it.md)
- **Reference:** [`docker/README_DOCKER.md`](docker/README_DOCKER.md)
  · 🇮🇹 [`docker/README_DOCKER.it.md`](docker/README_DOCKER.it.md)
- The in-app **Guide** tab repeats the first-run and update steps.

## Command line (optional)

Instead of the launcher, from the repository root:

```bash
docker compose -f docker/docker-compose.yml up --build   # first time / after update
docker compose -f docker/docker-compose.yml up           # normal start
docker compose -f docker/docker-compose.yml down          # stop
```

## Notes and limits

- The image builds natively for **linux/amd64** and **linux/arm64**. amd64 uses
  the exact conda lock `environment.yml`; arm64 (Apple Silicon) uses the
  version-pinned `docker/environment.arm64.yml`.
- Supported sensors (via Polymer's v4 API): Sentinel-3 OLCI, Sentinel-2 MSI,
  ENVISAT MERIS, MODIS Aqua, VIIRS, SeaWiFS, PRISMA, Landsat-8 OLI, ISS HICO.
- MODIS / VIIRS / SeaWiFS need **Level-1C** files prepared beforehand with NASA
  OBPG `l2gen` (not included here).

## Licence and citation

Polymer is distributed under the Polymer licence v2.0 — see
[`LICENCE.TXT`](LICENCE.TXT). Free for scientific/non-commercial use;
redistribution is not permitted.

When acknowledging Polymer in scientific work, cite:

> François Steinmetz, Pierre-Yves Deschamps, and Didier Ramon,
> "Atmospheric correction in presence of sun glint: application to MERIS",
> Opt. Express 19, 9783–9800 (2011). <http://dx.doi.org/10.1364/OE.19.009783>

> François Steinmetz and Didier Ramon, "Sentinel-2 MSI and Sentinel-3 OLCI
> consistent ocean colour products using POLYMER", Proc. SPIE 10778 (2018).
> <https://doi.org/10.1117/12.2500232>
