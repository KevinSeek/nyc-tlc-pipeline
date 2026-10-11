"""Download monthly TLC trip files and load them into the `raw` schema."""

from datetime import datetime
from pathlib import Path

import httpx

from . import config


def generate_raw_file_paths(year_month: str) -> tuple[str, Path, Path]:

    # Convert into a datetime type
    parsed_year_month = datetime.strptime(year_month, "%Y-%m")
    canonical = parsed_year_month.strftime("%Y-%m")

    raw_dir = config.NYC_TLC_DATA_DIR.joinpath("raw")
    act_path = raw_dir.joinpath(f"yellow_tripdata_{canonical}.parquet")
    tmp_path = raw_dir.joinpath(f"yellow_tripdata_{canonical}.parquet.part")

    return (canonical, tmp_path, act_path)


def download_raw_from_source(canonical: str, tmp_path: Path, act_path: Path) -> Path:

    # Build canonical url
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{canonical}.parquet"

    # Create the paths
    tmp_path.parent.mkdir(parents=True, exist_ok=True)

    time_out = httpx.Timeout(config.NYC_TLC_HTTP_READ_TIMEOUT_IN_SECONDS, connect=5)

    with httpx.Client(timeout=time_out) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()  # stop here for 404 / 500 / redirect
            with tmp_path.open("wb") as f:  # 'wb' = write, binary
                for chunk in response.iter_bytes():
                    f.write(chunk)

    # Promote file
    tmp_path.replace(act_path)
    return act_path
