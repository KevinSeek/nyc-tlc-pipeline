from datetime import UTC, datetime

import duckdb
from prefect import flow, get_run_logger

from . import config


@flow(name="smoke")
def smoke_flow() -> None:
    """Smoke Test:
    1. Duckdb is created or located at the right path
    2. Table and schema can be created if it is a fresh warehouse
    3. Path can be written. A single insertion into the DB.
    """
    # Get prefect logger
    logger = get_run_logger()

    duckdb_path = config.NYC_TLC_DUCKDB_PATH.resolve()

    logger.info("Image SHA: %s", config.NYC_TLC_IMAGE_SHA)
    logger.info("DUCKDB Abs Path: %s", duckdb_path)

    with duckdb.connect(str(duckdb_path)) as con:
        con.execute("""CREATE SCHEMA IF NOT EXISTS ops;""")
        con.execute(
            """
        CREATE OR REPLACE TABLE ops.smoke_check AS (
            SELECT 
                ? :: TIMESTAMPTZ AS checked_at, 
                ? :: VARCHAR AS image_sha
        );
        """,
            parameters=[datetime.now(UTC), config.NYC_TLC_IMAGE_SHA],
        )

    return None


def main() -> None:
    smoke_flow()

    return None
