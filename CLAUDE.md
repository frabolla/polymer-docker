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
- Image builds natively on amd64 and arm64; 42-test pytest suite passes
  (`test_quicklook.py` is skipped where xarray/netCDF4 are absent, e.g. the lean
  CI `test` job; it runs in the image).
- Container starts, `/_stcore/health` OK, UI loads in EN and IT, language
  persists, licence gate, all 5 tabs render, no runtime errors.
- Credential files written `0600`, `/data/config` is `0700`.
- `from polymer.main import run_atm_corr` imports cleanly.
- **Real PRISMA data test** (`~/Downloads/polymer-docker-master/data/input/PRS_L1_STD_OFFL_20260704102046…he5` + its `PRS_L2C_STD_…` companion, ~2.4 GB total; also cloned into this worktree's `data/input/`):
  `Level1_PRISMA` opens both files and initializes the product
  (`shape (1000, 1000)`). It then needs NASA Earthdata credentials to download
  meteo data — with a bad `.netrc` the run fails at that step with the humanised
  message. **A full successful Polymer run has never been completed** (needs a
  real NASA Earthdata account or Copernicus CDS key, which the user must supply
  in the Setup tab).

**NOT verified:**
- A full atmospheric correction producing a Level-2 file.
- The **Results tab** preview (`quicklook.list_2d_vars` / `make_png`) against a
  **real** Level-2. `quicklook.py` is now tested against a synthetic file with
  the exact layout `polymer/level2_nc.py` writes (dims `height`/`width`, one 2D
  variable per band named `Rw<wl>`), and band lookup matches the nearest
  wavelength within 20 nm so it works for hyperspectral sensors (PRISMA). Still
  unproven on an actual product.
- `credentials.test_earthdata` / `test_cds` against real valid accounts (only the
  401/"bad" path was seen). They are best-effort and never block saving.
- The Streamlit theme colours (light theme is applied; the teal primaryColor was
  not pixel-checked).

## 3. File map (`docker/`)

```
docker/
  Dockerfile                 multi-arch (TARGETARCH → env file), apt: git curl wget
                             tini make build-essential; compiles Cython; pins
                             streamlit>=1.40,<2; sets DIR_DATA/DIR_POLYMER_*/HOME
  docker-compose.yml         service "polymer"; port 127.0.0.1:8501; binds
                             ../data/{input,output,auxdata,ancillary,config};
                             shm_size 2gb; healthcheck on /_stcore/health;
                             build arg POLYMER_GUI_VERSION
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
    streamlit_app.py         the whole UI. Tabs: Processing / Setup / Guide /
                             Results / History
    i18n.py                  t() + EN/IT string table (_STRINGS); language saved
                             in /data/config/.polymer_lang
    params_schema.py         structural param data only (names/types/defaults)
    polymer_job.py           subprocess: builds Level1/Level2, calls
                             polymer.main.run_atm_corr (v4 API). resolve_sensor(),
                             _preflight(), _humanize_error(). Prints
                             "[polymer_job] BLOCKS_TOTAL n"; writes
                             <run_id>.result.json
    job_runner.py            one detached job at a time + queue; state in
                             /data/output/_run/; poll() heartbeat; cancel();
                             _prune(); failed_cfgs(); configure() for tests
    setup_status.py          verify_auxdata(), free_space_mb(),
                             list_input_products() (hides PRS_L2C_STD_*, adds
                             */GRANULE/*), prisma_l2c_name(),
                             missing_prisma_companion(), app_version()
    credentials.py           read/write ~/.netrc (NASA) and ~/.cdsapirc (CDS);
                             test_earthdata()/test_cds() best-effort HTTP checks
    uploads.py               st.file_uploader handler: .zip → safe-extract,
                             single-file products saved as-is
    quicklook.py             list_2d_vars(), make_png(path, out, var=None);
                             nearest-wavelength band match (±20 nm)
    aux_job.py               background download of the static auxdata: detached
                             `python -m polymer.get_auxdata`, state in
                             /data/output/_run/auxdata.*; start()/status()/
                             cancel()/clear(); worker mode `aux_job.py --run`
  launchers/
    Start-Polymer-macOS-Linux.command / Start-Polymer-Windows.bat
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
  2. `wget` (installed) + `/data/ancillary/METEO` (entrypoint) — the reader
     *always* builds `Ancillary_NASA()` in `__init__`, ignoring `ancillary=None`;
  3. a NASA Earthdata `.netrc` (or a CDS key) — the meteo download needs it,
     there is no climatology fallback for PRISMA.
  `polymer_job._preflight()` + the Processing tab check all three up-front
  (explicit message, Run disabled). `resolve_sensor()` maps `PRS_L1_*` /
  `PRS_L2C_*` → PRISMA even on "auto".
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
  `data/config/{.netrc,.cdsapirc,.polymer_licence_accepted,.polymer_lang}`,
  `data/auxdata`, `data/ancillary`, `data/output/{_jobs.log,_run/}`.

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

Real end-to-end test needs the ~1 GB auxdata (Setup tab, or `cp` from
`~/Downloads/polymer-docker-master/data/auxdata/`) **and** a real Level-1 product
in `data/input/` **and**, for PRISMA, NASA Earthdata credentials.

## 7. Known issues / open items (from the code review — none block v0.1.0)

Priority order:

1. **No full end-to-end run has ever succeeded** — needs data + credentials.
   Highest-value next step: the user adds their NASA Earthdata login, then run
   the PRISMA pair and see whether Polymer produces a Level-2 `.nc`. Then eyeball
   the Results tab preview against that file (`quicklook.py` now matches the
   layout `level2_nc.py` writes and is unit-tested, but a real product may still
   surprise it).
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
8. ~~auxdata download (Setup tab) is synchronous and uncancellable~~ — **done**:
   `aux_job.py` runs it as a detached subprocess with a Cancel button; the Setup
   tab polls (`time.sleep(2); st.rerun()`) like `render_running`. State survives
   reruns/tab switches. Still single-flight and still synchronous *inside* that
   worker (no resumable/partial download).
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
