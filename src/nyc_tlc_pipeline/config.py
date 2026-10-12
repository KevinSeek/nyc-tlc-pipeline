"""Defines the settings for the project and what their defaults are."""

import os
import pathlib


def get_env_path(env_var: str, default: str) -> pathlib.Path:
    return pathlib.Path(os.environ.get(env_var, default))


NYC_TLC_HTTP_READ_TIMEOUT_IN_SECONDS = int(
    os.environ.get("NYC_TLC_HTTP_READ_TIMEOUT_IN_SECONDS", "30")
)
NYC_TLC_DUCKDB_PATH = get_env_path("NYC_TLC_DUCKDB_PATH", "nyc_tlc.duckdb")
NYC_TLC_DATA_DIR = get_env_path("NYC_TLC_DATA_DIR", "data")
