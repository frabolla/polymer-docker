# CLAUDE.md — project context

Context for Claude Code sessions on this repository. Read this first.

## What this repository is

`frabolla/polymer-docker` is a **fork** of the open-source **Polymer** atmospheric
correction algorithm by HYGEOS (upstream: <https://github.com/hygeos/polymer>).

The fork adds **one thing**: a Docker container with a graphical web interface so
that non-technical users can install and run Polymer without a Python/conda
environment or the command line. **The Polymer algorithm code under `polymer/` is
upstream and is not modified here** — only `docker/`, `CLAUDE.md`, `.gitignore`
and the `README.md` were changed by this fork.

## Licence constraint (important)

`LICENCE.TXT` Section 2: Polymer may not be transferred/redistributed to third
parties "in any form, modified or unmodified". Consequences:

- **Never publish a pre-built image** to any public registry (GHCR, Docker Hub…).
  Only the *build recipe* is shipped; each user builds locally.
- The CI workflow (`.github/workflows/docker-build.yml`) runs the tests, then
  builds the image on native amd64 and arm64 runners to catch breakage — it
  **must never push** the image. It has a `concurrency` group so a new push
  cancels the previous run.
- The app shows `LICENCE.TXT` and requires the user to accept it on first run.

## Layout of the added code (`docker/`)

```
docker/
  Dockerfile                 micromamba env from environment.yml + Cython compile + Streamlit
  docker-compose.yml         service "polymer", binds ../data/*, linux/amd64
  Dockerfile.dockerignore    trimmed build context
  entrypoint.sh              prepares /data, links credentials, runs `streamlit run`
  app/
    streamlit_app.py         the whole UI (tabs: Processing / Setup / Guide / History)
    i18n.py                  translation layer: t(), EN/IT string table, lang persisted
    params_schema.py         structural param data only (names/types/defaults)
    polymer_job.py           subprocess wrapper around polymer.main.run_atm_corr (v4 API)
    setup_status.py          checks: compiled modules? auxdata? credentials?
    credentials.py           read/write ~/.netrc (NASA) and ~/.cdsapirc (CDS/ERA5)
    quicklook.py             PNG preview of a Level-2 product
  launchers/
    Start-Polymer-macOS-Linux.command / Start-Polymer-Windows.bat   double-click entry points
  README_DOCKER.md / .it.md  reference docs (EN / IT)
  HOWTO.md / .it.md          click-by-click guide for first-time Docker users (EN / IT)
.github/workflows/docker-build.yml   CI: build only, never push
```

## Key technical decisions

- **Base image**: `mambaorg/micromamba:1.5-jammy`, multi-arch. The Dockerfile
  picks the conda env file by `TARGETARCH`: `environment.yml` (exact linux-64
  lock) for amd64, `docker/environment.arm64.yml` (version floors only, solved
  fresh) for arm64. Keep `environment.arm64.yml` in sync with
  `pyproject.toml [tool.pixi.dependencies]` and the pip section of
  `environment.yml`.
- **Polymer API**: the v4 `run_atm_corr` (covers OLCI, MSI, MERIS, MODIS, VIIRS,
  SeaWiFS, PRISMA, Landsat-8, HICO). v5 (`main_v5.run_polymer`) is OLCI/PACE/HYPSO
  only, so not used.
- **`DIR_DATA=/data` env var is required at build & runtime**: `polymer/params.py`
  calls `core.env.getdir`, which *raises* if the fallback directory does not
  exist. `DIR_DATA`, `DIR_POLYMER_AUXDATA`, `DIR_POLYMER_ANCILLARY` are all set in
  the Dockerfile and the dirs are created before the first `import polymer`.
- **Cython build**: `make` inside the env (`meson setup build && meson compile`).
  Needs system `make` + `build-essential` (added via apt) plus `meson/ninja/cython`
  (in the conda env).
- **Auxiliary data (~1 GB incl. `LUT.hdf`) is NOT baked into the image** — it is
  downloaded on first run into the `data/auxdata` volume via the Setup tab
  (`python -m polymer.get_auxdata`).
- **Streamlit chrome hidden**: `--client.toolbarMode=minimal` + CSS in
  `streamlit_app.py` remove the "Deploy" button, the menu and the footer.
- **Persistent state** lives only in the bind-mounted `data/` folder:
  `data/config/.netrc`, `.cdsapirc`, `.polymer_licence_accepted`, `.polymer_lang`;
  `data/auxdata`, `data/ancillary`; `data/output/_jobs.log` (history).

## Localization

- English is primary; Italian is selectable in the sidebar and persisted in
  `data/config/.polymer_lang`.
- **All user-facing strings go through `i18n.t("key")`** — never hard-code UI text
  in `streamlit_app.py`. Add new keys to `_STRINGS` in `i18n.py` with **both**
  `en` and `it`, and keep `{placeholder}` names identical between languages.
- **Code comments and docstrings are in English.** No emoji in the UI (status uses
  the typographic marks `✓` / `–`).
- Doc files come in pairs: `*.md` (English) and `*.it.md` (Italian), cross-linked.

## Build / run / test

```bash
# build + run (from repo root)
docker compose -f docker/docker-compose.yml up -d --build
# UI: http://localhost:8501 (bound to 127.0.0.1)   health: /_stcore/health

# stop
docker compose -f docker/docker-compose.yml down

# app unit tests (no Docker; also run in CI before the build)
pytest docker/tests -q
# or inside the image:
docker run --rm --entrypoint micromamba -v "$PWD:/src:ro" -w /src polymer-gui:local \
  run -n polymer python -m pytest docker/tests -q

# quick import check inside the image
docker run --rm polymer-gui:local micromamba run -n polymer \
  python -c "import polymer.polymer_main, polymer.water; from polymer.main import run_atm_corr; print('ok')"
```

- A real end-to-end run needs the ~1 GB auxdata download **and** a real Level-1
  product in `data/input/` (Sentinel-3 `.SEN3`, Sentinel-2 `.SAFE`, PRISMA `.he5`,
  …). Upstream tests expect the user to supply sample files via
  `LEVEL1_SAMPLE_*` env vars — there is no bundled sample.
- What has been verified so far: image builds, UI loads, licence gate, tabs,
  language switch + persistence, credential files written `0600`,
  `from polymer.main import run_atm_corr` imports cleanly. A full atmospheric
  correction has **not** been run yet.

## Git / workflow conventions

- Default branch: `master`. Work branch used for this feature:
  `polymer-docker-container`.
- **Ask the user before every `git commit`, PR, or `git push`.** Staging and
  showing diffs is fine without asking.
- `gh` CLI is authenticated as `frabolla` and wired as git's credential helper
  (`gh auth setup-git`). Pushes from the shell work.
- Upstream `hygeos/polymer` is remote `upstream`. Do **not** open PRs against it
  (PRs #26/#27 there were closed on purpose).
- `data/` is git-ignored.

## App modules (docker/app/)

- `job_runner.py` — runs one Polymer job at a time as a detached subprocess,
  extra jobs queue. State in `/data/output/_run/` (`current.json`, `queue.json`,
  `<run_id>.log`, `<run_id>.result.json`). `poll()` is the idempotent heartbeat
  (finalize finished job → append `_jobs.log` → start next). `cancel()` kills the
  process group. The Processing tab polls with `time.sleep(2); st.rerun()` while a
  job runs.
- `polymer_job.py` — prints `[polymer_job] BLOCKS_TOTAL n` (best-effort: opens the
  Level-1 once to read shape) so the UI shows a real progress bar from the
  `Processing block:` lines Polymer emits; writes `<run_id>.result.json` on exit.
- `uploads.py` — `st.file_uploader` handler: `.zip` → safe-extract into
  `data/input`, single-file products saved as-is.
- `quicklook.py` — `list_2d_vars()` + `make_png(path, out, var=None)` (auto RGB /
  chlorophyll, or a chosen variable + histogram). Used by the Results tab.
- `setup_status.verify_auxdata()` — checks required aux files exist and are not
  truncated (min sizes); `auxdata_present()` uses it. `app_version()` reads
  `POLYMER_GUI_VERSION` env, then `/app/VERSION`, then "dev". `free_space_mb()`
  gates the Run / Download-auxdata buttons.
- `job_runner` also: `configure(dir)` (tests repoint paths), `_prune()` (keep
  `KEEP_RUNS` run file sets, cap `_jobs.log` at `JOBS_LOG_MAX_LINES`),
  `failed_cfgs(batch_id)` (for the "re-run failed" button; batch item lists are
  saved as `_run/batch_<id>.json`).
- `credentials.test_earthdata()` / `test_cds()` — best-effort HTTP checks used by
  the "Verify" buttons; return `("ok"|"bad"|"skip", detail)`, never block saving.
- Theme + chrome: `docker/app/.streamlit/config.toml` (light theme, minimal
  toolbar) is read because `entrypoint.sh` does `cd /app` before `streamlit run`.
  Favicon is `:material/water_drop:` (no emoji).
- Tests: `docker/tests/` (pytest, no Docker needed) — run in CI's `test` job
  before the image builds. Keep them green; `test_i18n.py` enforces the
  en/it + placeholder consistency that used to be a manual check.

## Known limitations / open items

- MODIS/VIIRS/SeaWiFS need Level-1C files prepared with NASA OBPG `l2gen`, not
  included.
- The HYGEOS git deps (`core`, `eoread`, `eotools`, `luts`) are pinned by commit
  inside `environment.yml` **and** `docker/environment.arm64.yml`; update both.
- No automated test of an actual processing run (needs data + credentials).
- `environment.arm64.yml` is solved fresh each build — a package could shift
  under it. Consider generating a real aarch64 lock later.
