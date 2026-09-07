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
- **macOS / Linux** → `Start-Polymer-macOS-Linux.command`
  (on macOS the first time: right-click → **Open** to get past Gatekeeper)

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
   Without credentials, Polymer still works using built-in climatologies.

## 5. Process a product

1. Copy your **Level-1** products into the `data/input/` folder that appeared
   next to the repository (`.SEN3` folders for Sentinel-3 OLCI, `.SAFE` for
   Sentinel-2 MSI, `.he5` files for PRISMA, `.N1` for MERIS, `.L1C` for
   MODIS/VIIRS/SeaWiFS…).
2. On the **Processing** tab: pick the product, the sensor (`auto` is fine in
   most cases; for **PRISMA** and **HICO** choose the sensor manually), the
   output format and the parameters.
3. Press **▶ Run Polymer**. The processing log scrolls on screen.
4. When done, the result is in `data/output/` and a preview is shown in the
   interface.

You can select **several products at once** for batch processing.

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
- MODIS/VIIRS/SeaWiFS need **Level-1C** files prepared beforehand with `l2gen`
  (NASA OBPG), which is not included here.
- The interface uses Polymer's v4 API (`run_atm_corr`), which covers every sensor
  listed above.
