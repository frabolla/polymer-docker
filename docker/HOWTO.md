# HOW-TO — Run Polymer for the first time (graphical, with Docker Desktop)

> 🇮🇹 Versione italiana: [HOWTO.it.md](HOWTO.it.md)

This guide is for someone who has **never used Docker** and wants to do
**everything with the mouse** — no commands, no text to type.

You use only three things:

1. **Docker Desktop** — an app with a normal window, buttons and menus.
2. **A launcher** — a file you double-click.
3. **The Polymer interface** — a normal web page in your browser.

Parts 1–3 are done once. After that, using Polymer is a double-click.

---

## Part 1 — Install Docker Desktop

### Windows 10 / 11

1. Download the installer:
   <https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe>
2. Double-click **`Docker Desktop Installer.exe`**.
3. Leave every option as proposed (keep **"Use WSL 2"** ticked) and click **OK**.
   If the installer offers to install extra Windows components, **accept**.
4. When it finishes, click **"Close and restart"**. Your PC restarts.
5. After the restart, open **Docker Desktop** from the Start menu.
6. In the window, click **Accept** on the *Docker Subscription Service Agreement*
   (free for personal use).
7. On the sign-in screen click **"Continue without signing in"**, then skip the
   survey.
8. Look near the clock (bottom-right of the screen, click the small **^** to show
   hidden icons): a whale icon 🐳 appears. Wait until it stops moving.

> If Windows shows a message that "WSL 2" is missing even after restarting, open
> Docker Desktop's own message — it has a **button** that installs it for you —
> or follow <https://docs.docker.com/desktop/setup/install/windows-install/>.

### macOS

1. Find out which Mac you have: click the **Apple menu ** (top-left) →
   **About This Mac**.
   - It says **"Chip: Apple M1 / M2 / M3 / M4"** → you have **Apple Silicon**.
   - It says **"Processor: Intel"** → you have **Intel**.
2. Download the matching installer:
   - Apple Silicon: <https://desktop.docker.com/mac/main/arm64/Docker.dmg>
   - Intel: <https://desktop.docker.com/mac/main/amd64/Docker.dmg>
3. Double-click the downloaded **`Docker.dmg`**. A window opens showing the
   **Docker** icon and an **Applications** folder — drag the Docker icon onto
   the Applications folder.
4. Open **Launchpad** or the **Applications** folder and click **Docker**.
5. A box says the app was downloaded from the Internet → click **Open**.
6. A box asks for **privileged access** → type your Mac login password and
   confirm (this happens only once).
7. Click **Accept** on the agreement, then **"Continue without signing in"**.
8. A whale icon 🐳 appears in the menu bar at the top of the screen. Wait until
   it stops moving.

### Linux

Install **Docker Desktop for Linux** by downloading the package for your
distribution from <https://docs.docker.com/desktop/setup/install/linux/> and
opening it with your software installer, then launch **Docker Desktop** from your
applications menu.

---

## Part 2 — Check that Docker Desktop is ready

1. Open the **Docker Desktop** window (click the whale icon 🐳, then
   **"Dashboard"** / **"Open Docker Desktop"** if needed).
2. Look at the **bottom-left corner** of the window: you should see a **green
   dot** and the words **"Engine running"**.

✅ If it says **"Engine running"**, you are ready. You can minimize the window;
leave the app open.

---

## Part 3 — Download Polymer

1. Open the project page on GitHub in your browser.
2. Click the green **`Code`** button, then **Download ZIP**.
3. Open your **Downloads** folder and **extract** (unzip) the file:
   - Windows: right-click the ZIP → **Extract All… → Extract**.
   - macOS: double-click the ZIP.
4. You now have a folder, e.g. **`polymer-docker-main`**. Drag it into your
   **Documents** folder so it is easy to find later.

---

## Part 4 — First start

1. Open the folder from Part 3, then open **`docker`**, then **`launchers`**.

2. **macOS only — one-time unlock.** A launcher taken from a downloaded ZIP is
   blocked by macOS (Gatekeeper) and is not marked runnable. Do this once:
   1. Open **Terminal** (press ⌘ + Space, type `Terminal`, press Return).
   2. In the Terminal window type `xattr -dr com.apple.quarantine ` (keep the
      space at the end), then **drag the project folder** from Finder onto the
      Terminal window and press **Return**.
   3. Type `chmod +x ` (again, keep the trailing space), **drag**
      `docker/launchers/Start-Polymer-macOS-Linux.command` from Finder onto the
      Terminal window, and press **Return**.

   (If you got the project with `git clone` instead of a ZIP, you can skip this —
   git keeps the file runnable.)

3. Double-click the file for your system:
   - **Windows** → **`Start-Polymer-Windows.bat`**
   - **macOS / Linux** → **`Start-Polymer-macOS-Linux.command`**

   **macOS — first time only:** if you still see *"cannot be opened because it is
   from an unidentified developer"* (or *"Apple could not verify…"*):
   right-click the file → **Open** → **Open**. If there is no **Open** button,
   go to  **System Settings → Privacy & Security**, scroll to the bottom, click
   **Open Anyway** next to the message about `Start-Polymer-macOS-Linux.command`,
   then confirm with **Open**. After this the normal double-click works.
   **Windows — first time only:** if a blue *"Windows protected your PC"* box
   appears, click **More info → Run anyway**.

4. A small window appears and shows text scrolling — this is just progress
   information. **You do not type anything in it.** You can move it aside.
   **The first start takes 10–20 minutes**: it is downloading and preparing the
   program. This happens **only once**.

5. When it is ready, your browser opens automatically at
   **<http://localhost:8501>**.
   If it does not open, type that address into your browser yourself, or use the
   Docker Desktop method in Part 7.

✅ You should see a page titled **"Polymer — Terms of use"**.

---

## Part 5 — Set up Polymer (in the web page)

### 5.1 Language

At the **top-left** of the page there is a **Language** menu. English is the
default; pick **Italiano** if you prefer. Your choice is remembered.

### 5.2 Accept the terms

Read the text, tick the box **"I have read and accept Polymer's Terms of use"**,
then click **Continue**.

### 5.3 Download the auxiliary data

1. Click the **Setup** tab.
2. Click the **"Download / update auxiliary data"** button.
3. Wait while it downloads about **1 GB** of reference tables. Text scrolls on
   the page to show progress. This is done **only once**.

✅ In the left sidebar, the line **"Static auxiliary data"** changes to a green
check ✅.

### 5.4 (Optional) Weather-data account

Polymer can fetch ozone / wind / pressure automatically if you have a free
account. Without one it still works for most sensors using built-in data — but
**PRISMA will not run** without a NASA Earthdata or Copernicus CDS account.

- **Setup** tab → **"Meteorological data source"** → choose **NASA Earthdata**
  or **Copernicus ERA5 / CDS**.
- Type your username and password (NASA) or your API key (CDS), then click
  **Save**. The sign-up links are shown right under the fields.

---

## Part 6 — Process a satellite product

1. Put your **Level-1** products into the **`data/input`** folder. This folder is
   **inside the folder you unzipped in Part 3**
   (`…/polymer-docker-main/data/input`). It appeared automatically at first
   start. Just drag your product folders/files into it with the mouse.

   Accepted: `.SEN3` folders (Sentinel-3 OLCI), `.SAFE` folders (Sentinel-2 MSI),
   `.he5` files (PRISMA), `.N1` files (MERIS), `.L1C` files
   (MODIS / VIIRS / SeaWiFS).

   **PRISMA takes two files:** the Level-1 (`PRS_L1_STD_OFFL_….he5`) **and** its
   Level-2C companion (`PRS_L2C_STD_….he5`, same name). Put **both** in
   `data/input`; select only the L1 in the interface. PRISMA also **requires a
   NASA Earthdata (or Copernicus CDS) account** for its weather data — add it in
   the Setup tab first. The interface tells you if either is missing and does
   not start.

   You can also use the **Upload a product** panel on the Processing tab: drop a
   `.zip` for folder products (`.SEN3` / `.SAFE`), or a single-file product.

2. Go back to the browser and **reload the page** (press **F5**, or ⌘R on Mac).
3. Click the **Processing** tab:
   - **Level-1 products to process** — click to pick one (or several, for batch
     processing).
   - **Sensor** — leave **auto**; the page shows the detected sensor. For
     **PRISMA** and **HICO** pick it from the list yourself.
   - **Output format** — `netcdf4` (recommended) or `hdf4`.
   - **Common parameters** — change only if you need to (number of CPU cores, an
     optional crop of the scene).
4. Click **Run Polymer**. A progress bar and the log update while it runs; a
   **Cancel** button stops it. It keeps going if you switch tabs.
5. When it finishes, the result file is in the **`data/output`** folder. If you
   ran several products, a summary table shows which succeeded and a button
   re-runs just the failed ones.
6. Open the **Results** tab to browse outputs: pick a file, choose a variable
   (or the automatic RGB / chlorophyll view), see a histogram, and click
   **Download this file**.

The **History** tab shows a table of your previous runs.

---

## Part 7 — Managing Polymer from the Docker Desktop window

Everything below is done with buttons in the Docker Desktop window — no typing.

1. Open **Docker Desktop** and click **Containers** in the left menu.
2. You see a row named **`polymer-gui`**.

| You want to… | Click… |
|---|---|
| **Open the interface** | the blue link **`8501:8501`** on that row — it opens the browser at the Polymer page |
| **Stop Polymer** | the **■ (Stop)** button on that row |
| **Start it again** | the **▶ (Start)** button on that row |
| **See what it is doing** | the container **name** → the **Logs** tab |
| **Delete it** (to rebuild fresh) | the **🗑 (Delete)** button — your `data/` folder is kept |

To start Polymer after your computer was switched off: make sure Docker Desktop
shows **"Engine running"**, then either double-click the launcher (Part 4) or
press **▶** on the `polymer-gui` row.

---

## Part 8 — Settings and repair (all in the Docker Desktop window)

Open **Docker Desktop**, then click the **gear icon ⚙ (Settings)** at the top.

- **Give Polymer more memory:** **Resources** → drag the **Memory** slider to at
  least **8 GB** → **Apply & restart**. Do this if processing stops with an
  "out of memory" message.
- **Start fresh if something is broken:** click the **bug icon 🐞 (Troubleshoot)**
  at the top → **"Clean / Purge data"** (or **"Reset to factory defaults"**).
  Then do Part 4 again (it will rebuild).
- **Free up disk space:** **Images** in the left menu → select **`polymer-gui`**
  → **Delete**. Your products and results in `data/` are not touched.

---

## Part 9 — Update to a new version

1. In Docker Desktop → **Containers** → press **■ (Stop)** on `polymer-gui`.
2. Download the new **ZIP** from GitHub and unzip it over the old folder
   (replace when asked), keeping your `data/` folder.
3. Double-click the launcher again. It rebuilds only what changed, which is
   quick.

---

## Common problems

| What you see | What to do |
|---|---|
| Launcher window says **"Docker is not running"** | Open Docker Desktop, wait for **"Engine running"** (bottom-left), then double-click the launcher again. |
| Whale icon 🐳 keeps moving / **"Docker Desktop starting…"** never ends | Right-click the whale → **Restart**. Still stuck → restart the computer. |
| Browser says **it can't connect** to `localhost:8501` | On the first start, wait a few more minutes. Then check Docker Desktop → **Containers**: the `polymer-gui` row should say **Running**. Click its **`8501:8501`** link. |
| Message **"port 8501 already in use"** | Another program is using that number. Close it, or open `docker/docker-compose.yml` with a text editor (Notepad / TextEdit), change `127.0.0.1:8501:8501` to `127.0.0.1:8502:8501`, save, restart Polymer, and use <http://localhost:8502>. |
| Processing stops with **"out of memory"** | Docker Desktop → ⚙ **Settings → Resources** → raise **Memory** to 8 GB+ → **Apply & restart**. |
| Processing is **slower than expected on an Apple Silicon Mac** | A native Apple-Silicon version is built automatically. If it still feels emulated, check Docker Desktop is not forcing "Rosetta" / `linux/amd64` for this image. |
| Nothing works, you want a clean slate | Docker Desktop → 🐞 **Troubleshoot → Clean / Purge data**, then redo Part 4. |

---

## Good to know

- Polymer belongs to HYGEOS and **must not be shared or redistributed** (see
  `LICENCE.TXT`). You build it on your own computer and accept the terms on the
  first page.
- Your products, results, downloads, language and settings all live in the
  **`data/`** folder next to the unzipped project — never inside Docker. You can
  delete and rebuild the container without losing them.
- MODIS / VIIRS / SeaWiFS need **Level-1C** files prepared in advance with
  `l2gen` (NASA OBPG); that step is not part of this tool.
