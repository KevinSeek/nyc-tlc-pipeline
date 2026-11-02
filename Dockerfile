# Base Image: Python 3.14 on Debian 13 (trixie); trixie pinned so a new Debian release can't change the OS silently 
# but tag still moves for Debian point & security releases and Python patch updates.
FROM python:3.14-slim-trixie

# Copy the uv binary from Astral's image (pinned to 0.13.1) into /bin
# COPY --from=<other image> <path inside OTHER image> <path inside MY image>
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /bin/

# Create `/app` and make it the directory that container starts in (i.e project root) 
# and base for relative paths in later `RUN`, `COPY` and `CMD` instruction.
WORKDIR /app

# Create Non-root runtime user + data directory (rarely change -> placed early so they stay cached).
# * Fixed UID makes volume ownership predictable across rebuilds and avoids host system UIDs (<1000).
# * `--create-home` gives `/home/app`, so Prefect can write `~/.prefect`.
RUN useradd --system --uid 10001 --create-home app
RUN mkdir /data && chown app:app /data

# Ensure all uv commands in this Dockerfile compile bytecode
# * Container runs as non-root `app`, which can't write `__pycache__` into the root-owned `.venv`
# * -> compile bytecode at build time instead.
ENV UV_COMPILE_BYTECODE=1

# Keep development dependencies (`pytest`, `ruff`) out of the runtime image.
# Replaces `--no-dev` on every `uv sync`.
ENV UV_NO_DEV=1

# Force the stdout and stderr streams to be unbuffered
# * By default, when Python detects it is not running in interactive terminal (e.g inside a detached Docker container)
# * It buffers `stdout` and `stderr` into blocks. This causes severe delays, making it look like your application has frozen.
ENV PYTHONUNBUFFERED=1

# Override the relative defaults in `config.py` so data goes to the volume, not the container layer
ENV NYC_TLC_DATA_DIR=/data
ENV NYC_TLC_DUCKDB_PATH=/data/nyc_tlc.duckdb

# Copy the 2 files that describe my dependencies
# * COPY takes space-separated sources; the last argument is the destination.
# * With multiple sources, the destination must end with `/` so it is treated as directory.
COPY pyproject.toml uv.lock ./

# Install the dependencies that are set in `uv.lock`
# * `--locked`: fail the build if `uv.lock` is out of sync with `pyproject.toml`
# * `--no-install-project`: skip own package; as `src/` isn't copied yet.
RUN uv sync --locked --no-install-project

# Copies application code and the declared files
# * README.md is required by the `uv_build` backend as it is declared in `pyproject.toml`
COPY README.md .
COPY src/ ./src/

# `uv sync` builds the package with the `uv_build` backend and installs it into `.venv`
# * Creates the [project.scripts] entries (i.e.`nyc-tlc-pipeline` and `nyc-tlc-smoke`) in `.venv/bin`
RUN uv sync --locked

# Prepend `/app/.venv/bin` to `$PATH` (the colon-separated list of directories searched for commands)
# * So `CMD` finds the console scripts (`nyc-tlc-pipeline`, `nyc-tlc-smoke`) without a full path; the venv's `python` also comes first.
ENV PATH="/app/.venv/bin:$PATH"

# Switch user; `RUN` commands from here run from new user.
# * Importantly, `.venv` stayed root-owned and read-only by "app" because `USER` comes after last `uv sync` 
# * and container will be run as `app` unless there is another USER command that comes after.
USER app

# Build-only variable with a default
# * Placed after the slow steps, a new SHA invalidates the caches from here down only
ARG NYC_TLC_IMAGE_SHA=local

# Make it visible at run time; 
# * Must match the `config.py` naming for the same variable else fails silently.
ENV NYC_TLC_IMAGE_SHA=$NYC_TLC_IMAGE_SHA

# Sets default command that triggers automatically when the container starts
# * Use bracketed list format to run programs in PID 1 instead of shell wrapper; to receive SIGTERM directly.
# * Use `CMD` instead of `ENTRYPOINT` so that command can be replaced by caller instead of appending to it.
CMD ["nyc-tlc-pipeline", "--help"]
