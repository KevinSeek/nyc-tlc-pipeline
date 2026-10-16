import argparse

from .config import RAW_DATA_DIR
from .ingestion import (
    TAXI_ZONE_LOOKUP_URL,
    YELLOW_TAXI_TRIPS_URL_TEMPLATE,
    download_raw_from_source,
    generate_parsed_and_canonical_date,
    generate_raw_taxi_zone_paths,
    generate_raw_trips_file_paths,
    load_raw_trips_to_duckdb,
    load_raw_zone_lookup_to_duckdb,
)
from .schema import RAW_SCHEMA, RAW_TAXI_ZONE_LOOKUP_TABLE, RAW_YELLOW_TAXI_TRIPS_TABLE


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

    trips_tmp_path, trips_act_path = generate_raw_trips_file_paths(
        RAW_DATA_DIR, string_ym
    )

    taxi_trips_url = YELLOW_TAXI_TRIPS_URL_TEMPLATE.format(year_month_string=string_ym)

    trips_act_file = download_raw_from_source(
        taxi_trips_url, tmp_path=trips_tmp_path, act_path=trips_act_path
    )

    row_count = load_raw_trips_to_duckdb(trips_act_file, parsed_ym)
    print(
        f"Loaded {string_ym}: {row_count} rows into {RAW_SCHEMA}.{RAW_YELLOW_TAXI_TRIPS_TABLE}"
    )

    # Taxi Zone section
    zone_tmp_path, zone_act_path = generate_raw_taxi_zone_paths(RAW_DATA_DIR)
    zone_act_file = download_raw_from_source(
        TAXI_ZONE_LOOKUP_URL, zone_tmp_path, zone_act_path
    )

    row_count = load_raw_zone_lookup_to_duckdb(zone_act_file)
    print(
        f"Loaded Taxi-Zone-Lookup: {row_count} rows into {RAW_SCHEMA}.{RAW_TAXI_ZONE_LOOKUP_TABLE}"
    )

    return None
