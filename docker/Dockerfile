# Polymer + web GUI, in a single container.
#
# LICENCE NOTE: this image must NOT be redistributed (LICENCE.TXT, Section 2).
# Every user builds it locally from this repository.
#
# Build (from the repository root):
#   docker compose -f docker/docker-compose.yml build
#
# Multi-architecture:
#   - linux/amd64 uses the exact conda-forge lock environment.yml
#   - linux/arm64 (Apple Silicon, etc.) uses docker/environment.arm64.yml, a
#     version-pinned but not build-locked spec solved fresh for aarch64
#
# Two stages: the builder has the C toolchain and compiles the Cython modules;
# the final image copies only the finished conda env + Polymer source, so
# build-essential / make / git (~250 MB) are not shipped.

# =========================================================================
# Stage 1 — builder: conda env + Cython compilation
# =========================================================================
FROM mambaorg/micromamba:1.5-jammy AS builder

ARG TARGETARCH
ARG POLYMER_GUI_VERSION=dev

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        git ca-certificates curl wget make build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- "polymer" conda environment ---
COPY environment.yml                 /tmp/environment.amd64.yml
COPY docker/environment.arm64.yml    /tmp/environment.arm64.yml
RUN set -eux; \
    case "${TARGETARCH:-amd64}" in \
      arm64|aarch64) ENVFILE=/tmp/environment.arm64.yml ;; \
      *)             ENVFILE=/tmp/environment.amd64.yml ;; \
    esac; \
    echo "Using $ENVFILE for TARGETARCH=${TARGETARCH:-amd64}"; \
    micromamba create -y -n polymer -f "$ENVFILE"; \
    micromamba run -n polymer pip install --no-cache-dir "streamlit>=1.40,<2"; \
    micromamba clean -y --all

ENV DIR_DATA=/data \
    DIR_POLYMER_AUXDATA=/data/auxdata/static \
    DIR_POLYMER_ANCILLARY=/data/ancillary \
    HOME=/data/config
RUN mkdir -p /data/auxdata/static /data/ancillary

# --- Polymer source + Cython module compilation ---
WORKDIR /opt/polymer
COPY polymer/     ./polymer/
COPY meson.build makefile pyproject.toml ./
COPY tools/       ./tools/
RUN micromamba run -n polymer make \
    && micromamba run -n polymer python -c "import polymer.polymer_main, polymer.water, polymer.clut, polymer.neldermead, polymer.polymer_minimizer; print('Cython modules OK')"

# =========================================================================
# Stage 2 — final image: runtime only, no C toolchain
# =========================================================================
FROM mambaorg/micromamba:1.5-jammy

ARG POLYMER_GUI_VERSION=dev

# wget: polymer.ancillary.Ancillary_NASA fetches meteo/ozone data.
# curl: container healthcheck. tini: PID 1.
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl wget tini \
    && rm -rf /var/lib/apt/lists/*

# The finished conda env and the compiled Polymer source, straight from builder.
COPY --from=builder /opt/conda/envs/polymer /opt/conda/envs/polymer
COPY --from=builder /opt/polymer            /opt/polymer

ENV MAMBA_DEFAULT_ENV=polymer \
    ENV_NAME=polymer \
    PATH=/opt/conda/envs/polymer/bin:$PATH \
    PYTHONPATH=/opt/polymer \
    PYTHONUNBUFFERED=1 \
    POLYMER_GUI_VERSION=$POLYMER_GUI_VERSION

# The data (input/output/auxdata/ancillary/config) lives here, on mounted volumes.
# The variables and the folders must already exist at build time: importing
# polymer, params.py resolves these directories via core.env.getdir, which RAISES
# if the folder does not exist. DIR_DATA is the shared fallback and must be set
# too (it is always evaluated, even when the other variables are defined).
ENV DIR_DATA=/data \
    DIR_POLYMER_AUXDATA=/data/auxdata/static \
    DIR_POLYMER_ANCILLARY=/data/ancillary \
    HOME=/data/config \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    NUMBA_NUM_THREADS=1 \
    MALLOC_ARENA_MAX=2
# The *_NUM_THREADS caps keep numpy's BLAS backends from spawning one thread pool
# per CPU (Polymer parallelises with processes, not threads). MALLOC_ARENA_MAX
# limits glibc malloc arenas, which trims resident memory for this workload.
RUN mkdir -p /data/input /data/output /data/auxdata/static /data/config \
             /data/ancillary /data/ancillary/METEO /data/ancillary/ERA5 \
    && micromamba run -n polymer python -c "import polymer.polymer_main, polymer.water; from polymer.main import run_atm_corr; print('Polymer import OK')"

# --- web GUI + licence + version (shown inside the app) ---
COPY docker/app/  /app/
COPY LICENCE.TXT  /app/LICENCE.TXT
COPY VERSION      /app/VERSION
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8501
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
