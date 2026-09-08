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
# The Cython modules are compiled here. The ~1 GB of static auxiliary data is
# NOT included: it is downloaded on first run into a mounted volume.

FROM mambaorg/micromamba:1.5-jammy

# BuildKit provides TARGETARCH automatically (amd64 / arm64).
ARG TARGETARCH
# Human-readable version, shown in the interface. Overridden by CI / releases.
ARG POLYMER_GUI_VERSION=dev

# --- system packages (git is needed for the pip dependencies hosted on GitHub) ---
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        git ca-certificates curl wget tini make build-essential \
    && rm -rf /var/lib/apt/lists/*
# wget is used by polymer.ancillary.Ancillary_NASA to fetch meteo/ozone data.

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
    OMP_NUM_THREADS=1
RUN mkdir -p /data/input /data/output /data/auxdata/static /data/config \
             /data/ancillary /data/ancillary/METEO

# --- Polymer source + Cython module compilation ---
WORKDIR /opt/polymer
COPY polymer/     ./polymer/
COPY meson.build makefile pyproject.toml ./
COPY tools/       ./tools/
RUN micromamba run -n polymer make \
    && micromamba run -n polymer python -c "import polymer.polymer_main, polymer.water, polymer.clut, polymer.neldermead, polymer.polymer_minimizer; print('Cython modules OK')"

# --- web GUI + licence + version (shown inside the app) ---
COPY docker/app/  /app/
COPY LICENCE.TXT  /app/LICENCE.TXT
COPY VERSION      /app/VERSION
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8501
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
