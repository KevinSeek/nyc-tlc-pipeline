"""Download monthly TLC trip files and load them into the `raw` schema."""

import hashlib
from datetime import UTC, date, datetime
from pathlib import Path

import duckdb
import httpx

from . import config, schema

YELLOW_TAXI_TRIPS_URL_TEMPLATE = (
    "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year_month_string}.parquet"
)
TAXI_ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"


def generate_parsed_and_canonical_date(year_month: str) -> tuple[date, str]:
    # Convert into a datetime type
    parsed_year_month = datetime.strptime(year_month, "%Y-%m").date()
    year_month_string = parsed_year_month.strftime("%Y-%m")
    return parsed_year_month, year_month_string


def generate_raw_trips_file_paths(raw_dir: Path, year_month_string: str) -> tuple[Path, Path]:

    act_path = raw_dir.joinpath(f"yellow_tripdata_{year_month_string}.parquet")
    tmp_path = raw_dir.joinpath(f"yellow_tripdata_{year_month_string}.parquet.part")

    return (tmp_path, act_path)


def generate_raw_taxi_zone_paths(raw_dir: Path) -> tuple[Path, Path]:
    act_path = raw_dir.joinpath("taxi_zone_lookup.csv")
    tmp_path = raw_dir.joinpath("taxi_zone_lookup.csv.part")

    return (tmp_path, act_path)


def download_raw_from_source(url: str, tmp_path: Path, act_path: Path) -> Path:

    # Create the directory
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


def load_raw_trips_to_duckdb(parquet_path: Path, source_month: date) -> int:

    # Read and get the hashvalue of the file
    with parquet_path.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()

    # Create casting statement from dictionary
    cast_list = ", ".join(
        [
            f'CAST("{key}" AS {data_type}) AS "{key}"'
            for key, data_type in schema.RAW_YELLOW_TAXI_TRIPS_COLUMNS.items()
        ]
    )

    tbl_name = f"{schema.RAW_SCHEMA}.{schema.RAW_YELLOW_TAXI_TRIPS_TABLE}"

    sql_stmt = f"""
    CREATE OR REPLACE TABLE {tbl_name} AS
        SELECT {cast_list},
        ? AS _file_sha256,
        ? AS _source_file,
        ? AS _loaded_at,
        ? AS _source_month
    FROM read_parquet(?);
    """

    with duckdb.connect(str(config.NYC_TLC_DUCKDB_PATH)) as con:
        con.execute(f"""CREATE SCHEMA IF NOT EXISTS {schema.RAW_SCHEMA};""")
        con.execute(
            sql_stmt,
            parameters=[
                digest,
                parquet_path.name,
                datetime.now(UTC),
                source_month,
                str(parquet_path),
            ],
        )
        return con.execute(f"SELECT count(*) FROM {tbl_name}").fetchone()[0]


def load_raw_zone_lookup_to_duckdb(csv_path: Path) -> int:
    # Read and get the hash value of the file
    with csv_path.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()

    # Create casting statement from dictionary
    cast_list = ", ".join(
        [
            f'CAST("{key}" AS {data_type}) AS "{key}"'
            for key, data_type in schema.RAW_TAXI_ZONE_LOOKUP_COLUMNS.items()
        ]
    )

    tbl_name = f"{schema.RAW_SCHEMA}.{schema.RAW_TAXI_ZONE_LOOKUP_TABLE}"
    sql_stmt = f"""
    CREATE OR REPLACE TABLE {tbl_name} AS
        SELECT {cast_list},
        ? AS _file_sha256,
        ? AS _source_file,
        ? AS _loaded_at
    FROM read_csv(?, all_varchar=true, header=true);
    """

    with duckdb.connect(str(config.NYC_TLC_DUCKDB_PATH)) as con:
        con.execute(f"""CREATE SCHEMA IF NOT EXISTS {schema.RAW_SCHEMA};""")
        con.execute(
            sql_stmt,
            parameters=[digest, csv_path.name, datetime.now(UTC), str(csv_path)],
        )
        return con.execute(f"SELECT count(*) FROM {tbl_name}").fetchone()[0]
