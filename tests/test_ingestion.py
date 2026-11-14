from datetime import date
from pathlib import Path

import duckdb
import pytest

from nyc_tlc_pipeline import config, schema
from nyc_tlc_pipeline.ingestion import (
    generate_parsed_and_canonical_date,
    generate_raw_taxi_zone_paths,
    generate_raw_trips_file_paths,
    load_raw_trips_to_duckdb,
)


def test_canonical_month_is_parsed_to_first_of_month() -> None:
    """Fails if a wrong date or string is returned: Corrupts _source_month and the file name."""
    arg = "2024-01"
    result = generate_parsed_and_canonical_date(arg)
    assert result == (date(2024, 1, 1), "2024-01")
    return None


def test_single_digit_month_is_canonicalised() -> None:
    """Fails if '2024-1' is not canonicalised: the file name and URL would not exist on TLC."""

    arg = "2024-1"
    result = generate_parsed_and_canonical_date(arg)
    assert result == (date(2024, 1, 1), "2024-01")
    return None


@pytest.mark.parametrize("year_month", ["2024-13", "202401", "2024-01-15", " 2024-01"])
def test_malformed_month_raises_value_error(year_month: str) -> None:
    """Fails if a malformed month is accepted:
    we'd build a URL/file name that doesn't exist on TLC.
    """

    with pytest.raises(ValueError):
        generate_parsed_and_canonical_date(year_month)

    return None


def test_correct_dir_and_year_month_generate_tmp_actual_paths() -> None:
    """Fails if a wrong temp and actual path is return:
    An incomplete download will write into an actual path instead
    """

    raw_dir = Path("raw")
    year_month = "2024-01"
    tmp_path, act_path = generate_raw_trips_file_paths(raw_dir, year_month)

    assert tmp_path == Path("raw").joinpath("yellow_tripdata_2024-01.parquet.part")
    assert act_path == Path("raw").joinpath("yellow_tripdata_2024-01.parquet")

    return None


def test_generate_zone_path_with_path_provision() -> None:
    """Fails if a wrong tmp and act path is returned:
    zone data may be saved to wrong path
    """

    raw_dir = Path("raw")
    tmp_path, act_path = generate_raw_taxi_zone_paths(raw_dir)

    assert act_path == Path("raw").joinpath("taxi_zone_lookup.csv")
    assert tmp_path == Path("raw").joinpath("taxi_zone_lookup.csv.part")

    return None


def test_trips_loader_writes_to_given_db_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fails if `db_path` is ignored by loader.
    Caller will overwrite the real table in `nyc_tlc.duckdb`
    """

    # Decoy: if the loader follows config, it writes here, not nyc_tlc.duckdb
    decoy = tmp_path.joinpath("fake_warehouse.duckdb")
    monkeypatch.setattr(config, "NYC_TLC_DUCKDB_PATH", decoy)

    db_path = tmp_path.joinpath("test.duckdb")
    fixture = Path(__file__).parent.joinpath("data", "yellow_tripdata_2024-01.parquet")

    row_count = load_raw_trips_to_duckdb(fixture, date(2024, 1, 1), db_path=db_path)

    # Test whether loader ignore the `db_path`
    assert not decoy.exists(), "Loader ignore `db_path` parameter and uses config default"

    with duckdb.connect(str(db_path), read_only=True) as con:
        loaded = con.execute(
            f"SELECT count(*) FROM {schema.RAW_SCHEMA}.{schema.RAW_YELLOW_TAXI_TRIPS_TABLE}"
        ).fetchone()[0]

    assert loaded == 100
    assert row_count == 100

    return None
