import argparse

from .ingestion import (
    download_raw_from_source,
    generate_parsed_and_canonical_date,
    generate_raw_file_paths,
    load_raw_to_duckdb,
)
from .schema import RAW_SCHEMA, RAW_YELLOW_TAXI_TRIPS_TABLE


def parse_arguments(arguments: list[str] | None = None) -> argparse.Namespace:
    """Parse the ingestion command arguments."""

    parser = argparse.ArgumentParser(
        description="Download one month of NYC yellow-taxi trips and load it into DuckDB."
    )

    parser.add_argument(
        "year_month",
        metavar="YYYY-MM",
        type=generate_parsed_and_canonical_date,
        help="Month to ingest",
    )

    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> None:

    # Retrieve the result from argparse Namespace
    parsed_arguments = parse_arguments(arguments)
    parsed_ym, string_ym = parsed_arguments.year_month

    tmp_path, act_path = generate_raw_file_paths(string_ym)
    act_path = download_raw_from_source(string_ym, tmp_path=tmp_path, act_path=act_path)

    row_count = load_raw_to_duckdb(act_path, parsed_ym)
    print(f"Loaded {string_ym}: {row_count} rows into {RAW_SCHEMA}.{RAW_YELLOW_TAXI_TRIPS_TABLE}")

    return None
