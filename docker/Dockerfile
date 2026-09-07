# check=skip=FromPlatformFlagConstDisallowed
# Polymer + web GUI, in a single container.
#
# LICENCE NOTE: this image must NOT be redistributed (LICENCE.TXT, Section 2).
# Every user builds it locally from this repository.
#
# Build (from the repository root):
#   docker compose -f docker/docker-compose.yml build
#
# The Python environment is recreated from the repo's conda-forge lock
# (environment.yml). Polymer's Cython modules are compiled here. The static
# auxiliary data is NOT included: it is downloaded on first run into a mounted
# volume.

# environment.yml is a conda lock for linux-64, so the image is amd64 only.
# On Apple Silicon Macs it runs under emulation (slower, but it works).
FROM --platform=linux/amd64 mambaorg/micromamba:1.5-jammy

# --- system packages (git is needed for the pip dependencies hosted on GitHub) ---
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        git ca-certificates curl tini make build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- "polymer" conda environment from the repo lock ---
COPY environment.yml /tmp/environment.yml
# The environment is selected with -n (the empty "name:" line in the file is ignored).
RUN micromamba create -y -n polymer -f /tmp/environment.yml \
    && micromamba run -n polymer pip install --no-cache-dir "streamlit>=1.36" \
    && micromamba clean -y --all

ENV MAMBA_DEFAULT_ENV=polymer \
    ENV_NAME=polymer \
    PATH=/opt/conda/envs/polymer/bin:$PATH \
    PYTHONPATH=/opt/polymer \
    PYTHONUNBUFFERED=1

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
RUN mkdir -p /data/input /data/output /data/auxdata/static /data/ancillary /data/config

# --- Polymer source + Cython module compilation ---
WORKDIR /opt/polymer
COPY polymer/     ./polymer/
COPY meson.build makefile pyproject.toml ./
COPY tools/       ./tools/
RUN micromamba run -n polymer make \
    && micromamba run -n polymer python -c "import polymer.polymer_main, polymer.water, polymer.clut, polymer.neldermead, polymer.polymer_minimizer; print('Cython modules OK')"

# --- web GUI + licence (shown inside the app) ---
COPY docker/app/  /app/
COPY LICENCE.TXT  /app/LICENCE.TXT
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8501
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
