# CLAUDE.md — project context

Read this first. It is the handoff for continuing the project in a new session.

## 1. What this repository is

`frabolla/polymer-docker` is a **fork** of the open-source **Polymer** atmospheric
correction algorithm by HYGEOS (upstream remote `upstream` →
<https://github.com/hygeos/polymer>).

The fork adds **one thing**: a Docker container with a graphical web interface so
non-technical users can run Polymer without a Python/conda environment or the
command line. **`polymer/` is upstream and is NOT modified here** — the fork only
touches `docker/`, `.github/workflows/`, `CLAUDE.md`, `README.md`, `.gitignore`,
`VERSION`.

Author of the packaging: **Francesco Tarini (@frabolla)** — credited in the UI
(sidebar, Guide tab, licence page) and the README.

### Licence constraint (hard rule)

`LICENCE.TXT` §2: Polymer may not be transferred/redistributed to third parties
"in any form". Therefore:

- **Never publish a pre-built image** to any registry (GHCR, Docker Hub…). Only
  the build recipe is shipped; every user builds locally and accepts the terms
  on first run (shown in the app).
- CI builds the image to catch breakage but **must never push** it.

## 2. Current status (as of v0.1.0, commit 4cf431f + uncommitted review fixes)

**Released:** git tag `v0.1.0` + GitHub Release exist (points at `4cf431f`).
`origin/master` and `origin/polymer-docker-container`… note: the remote branch
`polymer-docker-container` was **deleted**; only `origin/master` remains. Local
work continues on a local branch also named `polymer-docker-container` in the
worktree, pushed to `master` via `git push origin HEAD:master` (fast-forward).

**Verified working:**
- Image builds natively on amd64 and arm64 (multi-stage); 51-test pytest suite
  passes (`test_quicklook.py` is skipped where xarray/netCDF4 are absent, e.g.
  the lean CI `test` job; it runs in the image).
- Container starts, `/_stcore/health` OK, UI loads in EN and IT, language
  persists, licence gate. First launch shows the focused one-time setup page
  (no tabs); once modules + auxdata + a credential are all present it switches
  to the 5-tab layout (Processing first and bold). Verified both states + the
  sidebar footer + the polymer-chain logo + the "change folders" dialog render.
- Credential files written `0600`, `/data/config` is `0700`.
- `from polymer.main import run_atm_corr` imports cleanly.
- **Full end-to-end run — SUCCEEDED** (2026-09-08, arm64, image `test-e2e`).
  Real PRISMA pair `PRS_L1_STD_OFFL_20260704102046…he5` + `PRS_L2C_STD_…`
  (~2.4 GB) in `data/input/`, **Copernicus CDS / ERA5** key in the Setup tab,
  `ancillary="ERA5"`, `fmt="netcdf4"`, `multiprocessing=1`. cdsapi fetched the
  two bracketing ERA5 hours into `data/ancillary/ERA5/`, Polymer processed 10
  blocks in ~1 min, wrote a **46.7 MB Level-2 NetCDF**
  (`…he5.polymer.nc`, 70 data vars, dims `height=1000 width=1000`, `Rw406…Rw977`
  band vars). `job_runner` history row `result: ok`, `duration_s ≈ 140`.
- **Results tab preview against that real Level-2**: `quicklook.list_2d_vars`
  returned all 70 maps; `make_png` auto-RGB matched PRISMA bands by nearest
  wavelength (665→Rw664, 560→Rw559, 443→Rw446) and produced a sensible water
  RGB; `make_png(var="logchl")` produced the map+histogram. Task B confirmed on
  real data (the old exact-name band lookup would have failed here).

**NOT verified:**
- NASA Earthdata path end-to-end (only the CDS/ERA5 path has had a full run).
  `Ancillary_NASA` + `.netrc` still only seen failing on a bad login.
- `credentials.test_earthdata` / `test_cds` against real valid accounts (only the
  401/"bad" path was seen). They are best-effort and never block saving.
- The Streamlit theme colours (light theme is applied; the teal primaryColor was
  not pixel-checked).

## 3. File map (`docker/`)

```
docker/
  Dockerfile                 TWO stages. builder: apt git+make+build-essential,
                             solve the env (TARGETARCH → env file), compile
                             Cython. final: apt only ca-certificates curl wget
                             tini, COPY --from=builder the env + /opt/polymer.
                             Image 4.04 GB (was 4.95). final ENV also caps BLAS
                             thread pools (OPENBLAS/MKL/NUMEXPR/NUMBA_NUM_THREADS
                             =1, matching the existing OMP=1) and sets
                             MALLOC_ARENA_MAX=2 — idle RSS ~150 MB vs ~300.
  docker-compose.yml         service "polymer"; port 127.0.0.1:8501; binds
                             ../data/{auxdata,ancillary,config} plus
                             ${POLYMER_INPUT_DIR:-../data/input} and
                             ${POLYMER_OUTPUT_DIR:-../data/output} (the UI's
                             "change folders" dialog writes config/dirs.env; the
                             launcher passes it via `docker compose --env-file`).
                             env POLYMER_HOST_DIR (host path of data/, set by the
                             launchers) → shown in "Working folders". shm_size
                             1gb (was 2gb); commented mem_limit; healthcheck on
                             /_stcore/health
  environment.yml (repo root)  exact conda linux-64 lock (amd64) — UPSTREAM file
  docker/environment.arm64.yml version-floor spec for aarch64, solved fresh;
                             keep in sync with pyproject.toml [tool.pixi.deps]
                             and environment.yml's pip: section. pyepr is pip
                             (no conda-forge aarch64 build).
  Dockerfile.dockerignore    trims the build context (excludes docker/tests/ etc.)
  entrypoint.sh              mkdir /data/* incl. /data/ancillary/METEO; chmod
                             0700 /data/config, 0600 the credential files;
                             cd /app; exec `streamlit run`
  app/
    .streamlit/config.toml   light theme, toolbarMode=minimal, maxUploadSize=2048
    streamlit_app.py         the whole UI. is_configured() gates the layout:
                             NOT configured -> render_first_run() (focused
                             one-time setup page, no tabs); configured -> tabs in
                             priority order Processing / Results / Setup / History
                             / Guide, with Processing bold as the primary one.
                             Header: inline-SVG mark of a water drop drawn as a
                             polymer chain (no official Polymer logo ships).
                             render_sidebar() carries the fork note + the (small)
                             Francesco Tarini attribution at the sidebar bottom.
                             render_last_result() = success panel + chime +
                             download. render_folders() shows the host paths with
                             copy buttons + a "change input/output folders"
                             st.dialog (_workdirs_dialog).
    i18n.py                  t() + EN/IT string table (_STRINGS); language saved
                             in /data/config/.polymer_lang
    sound.py                 chime_wav_bytes(): a short success WAV built in
                             memory for st.audio(autoplay=True) (no audio asset)
    params_schema.py         structural param data only. OUTPUT_FORMATS =
                             ["hdf4", "netcdf4"] — HDF is the default output
    polymer_job.py           subprocess: builds Level1/Level2, calls
                             polymer.main.run_atm_corr (v4 API). resolve_sensor(),
                             _auto_ancillary_kind() (.netrc->nasa, .cdsapirc->
                             era5, else none — never assumes NASA), _preflight(),
                             _humanize_error(). Prints "[polymer_job]
                             BLOCKS_TOTAL n"; writes <run_id>.result.json
    job_runner.py            one detached job at a time + queue; state in
                             /data/output/_run/; poll() heartbeat; cancel();
                             _prune(); failed_cfgs(); configure() for tests
    setup_status.py          verify_auxdata(), free_space_mb(),
                             list_input_products() (hides PRS_L2C_STD_*, adds
                             */GRANULE/*), prisma_l2c_name(),
                             missing_prisma_companion(), app_version(),
                             load_workdirs()/save_workdirs()/clear_workdirs()
                             (input/output host-path override -> config/dirs.env)
    credentials.py           read/write ~/.netrc (NASA) and ~/.cdsapirc (CDS);
                             test_earthdata()/test_cds() best-effort HTTP checks
    uploads.py               st.file_uploader handler: .zip → safe-extract,
                             single-file products saved as-is
    quicklook.py             list_2d_vars(), make_png(path, out, var=None);
                             nearest-wavelength band match (±20 nm). Used only
                             for the optional "quick visual check" in Results —
                             Polymer's deliverable is the corrected file, not a
                             map. The per-variable / histogram map-builder UI was
                             removed.
    aux_job.py               background download of the static auxdata: detached
                             `python -m polymer.get_auxdata`, state in
                             /data/output/_run/auxdata.*; start()/status()/
                             cancel()/clear(); worker mode `aux_job.py --run`.
                             clear_stale_locks() deletes orphaned *.lock / *.tmp
                             under /data/auxdata before each attempt (a killed
                             download leaves core's LockFile behind → the next
                             run otherwise dies with "Timeout on Lockfile"); the
                             worker also retries once after cleaning.
  launchers/
    Start-Polymer-macOS-Linux.command / Start-Polymer-Windows.bat
       Pre-pull `mambaorg/micromamba:1.5-jammy` (retry ×3) before the build —
       BuildKit's `load metadata` step gives Docker Hub only ~10 s and fails the
       whole build on a slow/blocked network; `docker pull` retries and warns
       about VPN/proxy. The build itself is retried once. Also export
       POLYMER_HOST_DIR and, if data/config/dirs.env exists, add
       `--env-file data/config/dirs.env`.
  README_DOCKER.md / .it.md   reference docs (EN/IT)
  HOWTO.md / .it.md           click-by-click first-Docker-user guide (EN/IT)
  tests/                      pytest suite (no Docker needed) — CI `test` job
.github/workflows/docker-build.yml   test job → build on ubuntu-latest +
                             ubuntu-24.04-arm (native, both arches, every push);
                             concurrency group; NEVER pushes the image
VERSION                     "0.1.0" — read by app_version() (COPYd to /app/VERSION)
```

## 4. Key technical decisions & gotchas

- **Polymer API**: v4 `run_atm_corr(Level1(...), Level2(...))` — `Level2` is the
  OUTPUT object. Covers OLCI, MSI, MERIS, MODIS, VIIRS, SeaWiFS, PRISMA,
  Landsat-8, HICO. v5 (`main_v5.run_polymer`) is OLCI/PACE/HYPSO only → not used.
- **`DIR_DATA=/data` is required at build & runtime**: `polymer/params.py` calls
  `core.env.getdir`, which *raises* if a fallback dir is missing. `DIR_DATA`,
  `DIR_POLYMER_AUXDATA`, `DIR_POLYMER_ANCILLARY`, `HOME` are all ENV in the
  Dockerfile; the dirs are created (Dockerfile + entrypoint).
- **Bind mounts shadow build-time dirs.** Anything the container needs under
  `/data/*` at runtime must be created by `entrypoint.sh` (runs after mounts),
  not just the Dockerfile. This is why `/data/ancillary/METEO` is in the
  entrypoint.
- **Auxiliary data (~1 GB, incl. `LUT.hdf` ≈ 97 MB) is NOT baked in** — the user
  downloads it from the Setup tab (`python -m polymer.get_auxdata`) into
  `data/auxdata/`. `verify_auxdata()` checks a manifest with minimum sizes.
- **Cython build**: `make` inside the env needs system `make` + `build-essential`
  (apt) plus `meson/ninja/cython` (conda).
- **PRISMA needs THREE things** (`polymer/level1_prisma.py`):
  1. the L1 `PRS_L1_STD_OFFL_*.he5` **and** its L2C companion `PRS_L2C_STD_*.he5`
     in the same folder (the reader `assert`s the L2C exists);
  2. a meteo source — there is **no climatology fallback** for PRISMA. The reader
     defaults to `Ancillary_NASA()` **only when `ancillary is None`**; pass an
     `Ancillary_ERA5()` object and it uses ERA5. So `polymer_job` must resolve a
     concrete source: `build_ancillary("auto")` → `_auto_ancillary_kind()` picks
     `nasa` from a `.netrc`, else `era5` from a `.cdsapirc` (never assume NASA).
  3. the source's folder + tooling:
     - NASA: `wget` (installed) + `/data/ancillary/METEO` (entrypoint mkdir);
     - ERA5: `cdsapi` (installed) + `/data/ancillary/ERA5` (entrypoint mkdir) —
       `ERA5.__init__` raises if that dir is absent. Older images that predate
       this mkdir fail with a misleading "could not download" message.
  `polymer_job._preflight()` + the Processing tab check the pair + that *some*
  credential exists (`.netrc` earthdata OR `.cdsapirc`) up-front (explicit
  message, Run disabled). `resolve_sensor()` maps `PRS_L1_*` / `PRS_L2C_*` →
  PRISMA even on "auto".
  Confirmed end-to-end on 2026-09-08 via the ERA5/CDS path (see §2).
- **Error messages**: `polymer_job._humanize_error(tb)` maps common failures
  (NASA auth, `polymer/ancillary.py` in the traceback, "Unable to detect sensor",
  missing `LUT.hdf`/auxdata, missing METEO dir, missing wget, MemoryError) to one
  plain actionable sentence stored in `<run_id>.result.json` `error` and shown in
  the batch summary + History (`error` column + per-row `st.error`). The full
  traceback stays in `_run/<id>.log`.
- **Streamlit chrome** hidden: `[client] toolbarMode="minimal"` in config.toml +
  CSS in `streamlit_app.py`. Favicon `:material/water_drop:` (no emoji anywhere).
- **`render_running`** polls with `time.sleep(2); st.rerun()` while a job runs —
  the standard Streamlit pattern; it re-executes the whole page every 2 s.
- **Persistent state** lives only in the bind-mounted `data/`:
  `data/config/{.netrc,.cdsapirc,.polymer_licence_accepted,.polymer_lang,
  dirs.env}`, `data/auxdata`, `data/ancillary`, `data/output/{_jobs.log,_run/}`.
  `dirs.env` (optional) holds `POLYMER_INPUT_DIR` / `POLYMER_OUTPUT_DIR` when the
  user moved those folders; the launcher feeds it to `docker compose --env-file`.

## 5. Localization rules

- English is primary; Italian selectable in the sidebar.
- **Every user-facing string goes through `i18n.t("key")`.** Add keys to
  `_STRINGS` with BOTH `en` and `it`, identical `{placeholder}` names.
  `docker/tests/test_i18n.py` enforces this + that `streamlit_app.py` only uses
  defined keys.
- **Code comments & docstrings in English.** No emoji in the UI (status uses `✓` /
  `–`).
- Doc files come in `*.md` / `*.it.md` pairs, cross-linked.

## 6. Build / run / test

```bash
# from repo root
docker compose -f docker/docker-compose.yml up -d --build   # UI: http://localhost:8501
docker compose -f docker/docker-compose.yml down

# app unit tests (also run in CI before the image build)
pytest docker/tests -q
docker run --rm --entrypoint micromamba -v "$PWD:/src:ro" -w /src polymer-gui:local \
  run -n polymer python -m pytest docker/tests -q

# run a job by hand inside the container (bypasses the UI)
docker exec polymer-gui sh -lc 'cd /app && micromamba run -n polymer python polymer_job.py \
  --config /tmp/job.json --run-id x --result /tmp/r.json'   # see polymer_job.py docstring for job.json

# quick import check
docker run --rm --entrypoint micromamba polymer-gui:local run -n polymer \
  python -c "import polymer.polymer_main, polymer.water; from polymer.main import run_atm_corr; print('ok')"
```

Real end-to-end test needs the auxdata (Setup tab → "Download auxiliary data",
~190 MB verified by the manifest) **and** a real Level-1 product in `data/input/`
**and**, for PRISMA, a NASA Earthdata *or* Copernicus CDS account.

## 7. Known issues / open items (from the code review — none block v0.1.0)

Priority order:

1. ~~No full end-to-end run has ever succeeded~~ — **done** 2026-09-08: PRISMA +
   CDS/ERA5 produced a 46.7 MB Level-2 NetCDF and the Results-tab preview
   rendered (see §2). Remaining gap: the **NASA Earthdata** path has never had a
   full run; and only `multiprocessing=1` was exercised (higher values on an
   8 GB Docker VM with a hyperspectral cube may OOM — untested).
2. **Browser upload of multi-GB products is impractical** — Streamlit holds the
   whole file in memory; `maxUploadSize` is 2 GB. Copying into `data/input/` is
   the real path (documented). Fine as-is; do not "fix" by raising the limit
   further.
3. `credentials.test_earthdata` / `test_cds` endpoints + auth scheme are
   unverified with real valid accounts — a valid account might show "bad".
   Best-effort, never blocks saving; revisit if users complain.
4. `estimate_total_blocks` still opens non-PRISMA Level-1 products twice (once to
   probe shape, once for the real run). PRISMA is now skipped. Minor I/O waste.
5. PRISMA + `ancillary="none"` in the UI is effectively ignored (the reader
   forces `Ancillary_NASA`). Could disable "none" for PRISMA or document it.
6. Base image `mambaorg/micromamba:1.5-jammy` is pinned by minor tag, not digest.
7. `environment.arm64.yml` is solved fresh each build — a transitive package
   could shift under it. A real `conda-lock` aarch64 lock would pin it.
7b. **Image size ~4.0 GB is expected and near-irreducible.** Breakdown: the conda
   env ~3.0 GB (gdal, numba/llvmlite, scipy/pandas/xarray/dask, netcdf4, h5py,
   pyhdf, rasterio, eccodes, matplotlib, glymur, shapely, pyproj …), Ubuntu base
   ~80 MB, runtime apt (curl/wget/tini) ~30 MB, Cython .so ~17 MB. gdal + the
   scientific stack is the floor. **RAM**: the container idles ~150 MB; the ~6 GB
   a Windows user sees is the WSL2/Docker-Desktop VM *reservation*, tunable in
   Docker Desktop → Resources → Memory or `%UserProfile%\.wslconfig`
   (`[wsl2]` / `memory=4GB`). Documented in HOWTO Part 8.
8. ~~auxdata download (Setup tab) is synchronous and uncancellable~~ — **done**:
   `aux_job.py` detached subprocess + Cancel; the Setup tab polls like
   `render_running`. Single-flight. Not resumable *inside* one run, but it skips
   files already on disk, `clear_stale_locks()` clears orphaned `.lock`/`.tmp`
   first, and the worker retries once — so a killed download (common on Windows)
   recovers on the next "Retry". If `verify_auxdata()` passes the section
   early-returns (no re-download). The static data is mandatory — no skip button
   (it is the atm-correction LUTs, unrelated to the meteo credentials).
9. macOS bind-mount directory perms may not honour `chmod 700` on `data/config`
   (the credential *files* get 0600, which is what matters).
10. `_finalize` `duration_s` is wall-clock; for a job orphaned by a container
    stop it can be huge (the row now carries a clear "did not finish" error).

## 8. Git / workflow conventions

- Default branch `master`. **Ask the user before every `git commit`, PR, or
  `git push`** (staging + showing diffs is fine without asking). The user pushes
  and opens PRs themselves via GitHub Desktop unless they explicitly ask you to.
- `gh` is authenticated as `frabolla` and wired as git's credential helper. When
  asked to push, the pattern is: local branch → `git push origin HEAD:master`
  (fast-forward). Then the user `git pull`s in the main checkout
  `/Users/francesco/ClaudeCode/polymer-docker`.
- Do NOT open PRs against `upstream` (hygeos/polymer) — PRs #26/#27 there were
  closed on purpose.
- `data/` is git-ignored (`.DS_Store` too).
- This worktree: `.claude/worktrees/polymer-docker-container-2c853f`. Its `data/`
  currently holds the real PRISMA test pair (CoW clones, ~0 disk) and a cloned
  `data/auxdata` — kept for the next session's end-to-end test.

## 9. First steps for a new session

1. `docker compose -f docker/docker-compose.yml up -d --build`, open
   http://localhost:8501, accept the licence.
2. If continuing the PRISMA test: Setup tab → enter the user's real NASA
   Earthdata username/password → Verify → Save. (You cannot enter credentials
   yourself — ask the user to.)
3. Processing tab → the PRISMA L1 is pre-listed → Run Polymer → watch for a
   Level-2 in `data/output/` → check the Results tab preview.
4. Any commit/push: ask first.
