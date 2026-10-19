# Base image: Python 3.14 on Debian 13 (trixie); trixie pinned so a new Debian release can't change the OS silently.
FROM python:3.14-slim-trixie

# Copy the uv binary from Astral's image (pinned to 0.13.1) into /bin, which is already on PATH.
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /bin/

# Create `/app` and make it the working directory (e.g. project root) for every later instruction.
WORKDIR /app

# Non-root runtime user + data directory (rarely change -> placed early so they stay cached).
# Fixed UID makes volume ownership predictable across rebuilds and avoids host system UIDs (<1000).
# `--create-home` gives `/home/app`, so Prefect can write `~/.prefect`.
RUN useradd --system --uid 10001 --create-home app
# `/data` is an absolute path at the filesystem root (not under /app); owned by `app`.
# A named volume mounted at `/data` copies this ownership on first mount.
RUN mkdir /data && chown app:app /data

# ENV sets an environment variable for later build steps and for the running container.
# Container runs as non-root `app`, which can't write `__pycache__` into the root-owned `.venv`
# -> compile bytecode at build time instead.
ENV UV_COMPILE_BYTECODE=1
# Keep dev dependencies (`pytest`, `ruff`) out of the runtime image; replaces `--no-dev` on every `uv sync`.
ENV UV_NO_DEV=1
# Python flushes logs immediately, so output shows up in `docker logs` without delay.
ENV PYTHONUNBUFFERED=1
# Override the relative defaults in `config.py` so data goes to the volume, not the image layer.
ENV NYC_TLC_DATA_DIR=/data
ENV NYC_TLC_DUCKDB_PATH=/data/nyc_tlc.duckdb

# COPY takes space-separated sources; the last argument is the destination.
# With multiple sources, the destination must end with `/` so it is treated as a directory.
# Copy only the dependency files -> cached layer; editing `src/` won't re-run `uv sync`.
COPY pyproject.toml uv.lock ./
# Install dependencies only (not the project itself); `--locked` fails if uv.lock is out of date.
RUN uv sync --locked --no-install-project

# Install own package: README.md is required by the `uv_build` backend.
COPY README.md .
COPY src/ ./src/
# `uv sync` builds the package with the `uv_build` backend and installs it into `.venv`
# (creates the `nyc-tlc-pipeline` and `nyc-tlc-smoke` scripts in `.venv/bin`).
RUN uv sync --locked
# So CMD can find the scripts without a full path.
# `$PATH` inside `ENV` expands to the base image's current PATH.
ENV PATH="/app/.venv/bin:$PATH"

# Switch user: everything after this line, and the running container, runs as `app`.
# Placed after the last `uv sync` so `.venv` stays root-owned (read-only for `app`).
USER app

# Image SHA: ARG exists only during the build; set with `--build-arg NYC_TLC_IMAGE_SHA=<sha>`.
# Default `local` matches `config.py` and signals no SHA was passed (e.g. a quick local build).
# Placed after the slow steps: a new value only invalidates the cache from this line on.
ARG NYC_TLC_IMAGE_SHA=local
# Carry the ARG into the running container (the smoke flow logs it).
ENV NYC_TLC_IMAGE_SHA=$NYC_TLC_IMAGE_SHA

# Default command; compose overrides it with `nyc-tlc-smoke`.
# JSON array (exec) form: each element is one argument, no shell in between.
# The program runs as PID 1, so `docker stop` (SIGTERM) reaches it directly and it can shut down cleanly.
CMD ["nyc-tlc-pipeline", "--help"]
